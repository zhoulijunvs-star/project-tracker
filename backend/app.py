"""
Project Tracker API - FastAPI 应用主入口
提供完整的 REST API + 静态文件服务
"""

import os
import sys
import json
import re
from datetime import datetime, date
from io import BytesIO
from typing import Optional, List
from collections import defaultdict

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case

from database import get_db, db_session, engine
from models import Base, Customer, Project, SupplierQuote, PriceReference

# ── App Setup ──────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'uploads'), exist_ok=True)

app = FastAPI(title='Project Tracker', version='1.0.0')

# ── 确保表已创建 ──────────────────────────────────────────
Base.metadata.create_all(bind=engine)


# ════════════════════════════════════════════════════════════
#  Customer APIs
# ════════════════════════════════════════════════════════════

@app.get('/api/customers')
def list_customers(search: str = '', db: Session = Depends(get_db)):
    q = db.query(Customer)
    if search:
        kw = f'%{search}%'
        q = q.filter(
            Customer.company_name.ilike(kw) |
            Customer.contact_name.ilike(kw) |
            Customer.phone.ilike(kw)
        )
    return q.order_by(Customer.updated_at.desc()).all()


@app.get('/api/customers/{customer_id}')
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(Customer).get(customer_id)
    if not c:
        raise HTTPException(404, '客户不存在')
    return c


@app.post('/api/customers')
def create_customer(data: dict, db: Session = Depends(get_db)):
    c = Customer(
        company_name=data.get('company_name', ''),
        address=data.get('address', ''),
        contact_name=data.get('contact_name', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@app.put('/api/customers/{customer_id}')
def update_customer(customer_id: int, data: dict, db: Session = Depends(get_db)):
    c = db.query(Customer).get(customer_id)
    if not c:
        raise HTTPException(404, '客户不存在')
    for field in ['company_name', 'address', 'contact_name', 'phone', 'email']:
        if field in data:
            setattr(c, field, data[field])
    db.commit()
    return c


@app.delete('/api/customers/{customer_id}')
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(Customer).get(customer_id)
    if not c:
        raise HTTPException(404, '客户不存在')
    db.delete(c)
    db.commit()
    return {'ok': True}


# ════════════════════════════════════════════════════════════
#  Project APIs
# ════════════════════════════════════════════════════════════

@app.get('/api/projects')
def list_projects(
    search: str = '',
    customer_id: Optional[int] = None,
    is_landed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Project)
    if search:
        kw = f'%{search}%'
        q = q.filter(Project.name.ilike(kw) | Project.description.ilike(kw))
    if customer_id:
        q = q.filter(Project.customer_id == customer_id)
    if is_landed is not None:
        q = q.filter(Project.is_landed == is_landed)
    return q.order_by(Project.updated_at.desc()).all()


@app.get('/api/projects/{project_id}')
def get_project(project_id: int, db: Session = Depends(get_db)):
    p = db.query(Project).get(project_id)
    if not p:
        raise HTTPException(404, '项目不存在')
    return {
        **serialize(p),
        'customer': serialize(db.query(Customer).get(p.customer_id)),
        'supplier_quotes': [serialize(q) for q in p.supplier_quotes],
    }


@app.post('/api/projects')
def create_project(data: dict, db: Session = Depends(get_db)):
    p = Project(
        name=data.get('name', ''),
        description=data.get('description', ''),
        customer_id=data['customer_id'],
        quotation_date=parse_date(data.get('quotation_date')),
        final_price=data.get('final_price'),
        final_price_notes=data.get('final_price_notes', ''),
        final_margin=data.get('final_margin'),
        final_margin_notes=data.get('final_margin_notes', ''),
        cost_price=data.get('cost_price'),
        is_landed=data.get('is_landed', False),
        landed_date=parse_date(data.get('landed_date')),
        category=data.get('category', ''),
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    # Handle supplier quotes
    quotes = data.get('supplier_quotes', [])
    for qd in quotes:
        q = SupplierQuote(
            project_id=p.id,
            supplier_company=qd.get('supplier_company', ''),
            contact_name=qd.get('contact_name', ''),
            phone=qd.get('phone', ''),
            email=qd.get('email', ''),
            product_service_detail=qd.get('product_service_detail', ''),
            price=qd.get('price'),
            currency=qd.get('currency', 'CNY'),
            category=qd.get('category', ''),
        )
        db.add(q)
    db.commit()

    # Update price references
    update_price_references(db)
    return get_project(p.id, db)


@app.put('/api/projects/{project_id}')
def update_project(project_id: int, data: dict, db: Session = Depends(get_db)):
    p = db.query(Project).get(project_id)
    if not p:
        raise HTTPException(404, '项目不存在')

    fields = ['name', 'description', 'customer_id', 'final_price', 'final_price_notes',
              'final_margin', 'final_margin_notes', 'cost_price', 'is_landed', 'category']
    for f in fields:
        if f in data:
            setattr(p, f, data[f])
    if 'quotation_date' in data:
        p.quotation_date = parse_date(data['quotation_date'])
    if 'landed_date' in data:
        p.landed_date = parse_date(data['landed_date'])

    # Replace supplier quotes if provided
    if 'supplier_quotes' in data:
        db.query(SupplierQuote).filter(SupplierQuote.project_id == project_id).delete()
        for qd in data['supplier_quotes']:
            q = SupplierQuote(
                project_id=p.id,
                supplier_company=qd.get('supplier_company', ''),
                contact_name=qd.get('contact_name', ''),
                phone=qd.get('phone', ''),
                email=qd.get('email', ''),
                product_service_detail=qd.get('product_service_detail', ''),
                price=qd.get('price'),
                currency=qd.get('currency', 'CNY'),
                category=qd.get('category', ''),
            )
            db.add(q)

    db.commit()
    update_price_references(db)
    return get_project(project_id, db)


@app.delete('/api/projects/{project_id}')
def delete_project(project_id: int, db: Session = Depends(get_db)):
    p = db.query(Project).get(project_id)
    if not p:
        raise HTTPException(404, '项目不存在')
    db.delete(p)
    db.commit()
    update_price_references(db)
    return {'ok': True}


# ════════════════════════════════════════════════════════════
#  Supplier Quote APIs
# ════════════════════════════════════════════════════════════

@app.get('/api/projects/{project_id}/quotes')
def list_quotes(project_id: int, db: Session = Depends(get_db)):
    return db.query(SupplierQuote).filter(
        SupplierQuote.project_id == project_id
    ).order_by(SupplierQuote.id).all()


# ════════════════════════════════════════════════════════════
#  Dashboard APIs
# ════════════════════════════════════════════════════════════

@app.get('/api/dashboard/summary')
def dashboard_summary(
    year: Optional[int] = None,
    period: str = 'month',  # month | quarter | year
    db: Session = Depends(get_db)
):
    """看板汇总：落地统计、毛利、金额"""
    q = db.query(Project)
    if year:
        q = q.filter(extract('year', Project.created_at) == year)

    projects = q.all()
    total_count = len(projects)
    landed_count = sum(1 for p in projects if p.is_landed)
    win_rate = round(landed_count / total_count * 100, 1) if total_count > 0 else 0
    total_final_price = sum(p.final_price or 0 for p in projects)
    total_margin = sum(p.final_margin or 0 for p in projects)

    # Group by period
    groups = defaultdict(lambda: {'count': 0, 'landed': 0, 'price': 0.0, 'margin': 0.0})

    for p in projects:
        d = p.quotation_date or p.created_at.date() if p.created_at else date.today()
        if period == 'month':
            key = f'{d.year}-{d.month:02d}'
        elif period == 'quarter':
            key = f'{d.year}-Q{(d.month - 1) // 3 + 1}'
        else:
            key = str(d.year)
        groups[key]['count'] += 1
        if p.is_landed:
            groups[key]['landed'] += 1
        groups[key]['price'] += (p.final_price or 0)
        groups[key]['margin'] += (p.final_margin or 0)

    sorted_groups = sorted(groups.items())

    return {
        'summary': {
            'total_count': total_count,
            'landed_count': landed_count,
            'win_rate': win_rate,
            'total_final_price': round(total_final_price, 2),
            'total_margin': round(total_margin, 2),
        },
        'groups': [
            {
                'period': k,
                'count': v['count'],
                'landed': v['landed'],
                'price': round(v['price'], 2),
                'margin': round(v['margin'], 2),
            }
            for k, v in sorted_groups
        ],
    }


# ════════════════════════════════════════════════════════════
#  Price Reference APIs
# ════════════════════════════════════════════════════════════

@app.get('/api/price-references')
def list_price_references(
    search: str = '',
    category: str = '',
    db: Session = Depends(get_db)
):
    q = db.query(PriceReference)
    if search:
        kw = f'%{search}%'
        q = q.filter(PriceReference.product_service_name.ilike(kw))
    if category:
        q = q.filter(PriceReference.category == category)
    return q.order_by(PriceReference.category, PriceReference.updated_at.desc()).all()


@app.get('/api/price-references/categories')
def list_price_categories(db: Session = Depends(get_db)):
    cats = db.query(PriceReference.category).distinct().order_by(PriceReference.category).all()
    return [c[0] for c in cats]


def update_price_references(db: Session):
    """Rebuild price_references from all supplier_quotes"""
    db.query(PriceReference).delete()
    quotes = db.query(SupplierQuote).all()

    # Group by (category, product_service_detail)
    groups = defaultdict(list)
    for q in quotes:
        key = (q.category or '未分类', q.product_service_detail or '未指定')
        groups[key].append(q)

    for (cat, name), qlist in groups.items():
        prices = [q.price for q in qlist if q.price is not None]
        currencies = list(set(q.currency for q in qlist if q.currency))
        suppliers = list(set(q.supplier_company for q in qlist if q.supplier_company))
        latest = max((q.created_at for q in qlist if q.created_at), default=datetime.now())

        ref = PriceReference(
            category=cat,
            product_service_name=name,
            avg_price=round(sum(prices) / len(prices), 2) if prices else None,
            min_price=min(prices) if prices else None,
            max_price=max(prices) if prices else None,
            currency=currencies[0] if len(currencies) == 1 else 'MIXED',
            quote_count=len(qlist),
            supplier_list=json.dumps(suppliers, ensure_ascii=False),
            latest_quote_date=latest.date() if hasattr(latest, 'date') else latest,
        )
        db.add(ref)

    db.commit()


# ════════════════════════════════════════════════════════════
#  Import APIs (PDF / Excel)
# ════════════════════════════════════════════════════════════

@app.post('/api/import/quote')
async def import_quote(
    file: UploadFile = File(...),
    project_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """导入供应商报价文件（PDF/Excel），自动解析并入库"""
    content = await file.read()
    ext = os.path.splitext(file.filename)[1].lower()

    if ext in ('.xlsx', '.xls'):
        parsed = parse_excel_quote(content)
    elif ext == '.pdf':
        parsed = parse_pdf_quote(content)
    elif ext == '.csv':
        parsed = parse_csv_quote(content)
    else:
        raise HTTPException(400, f'不支持的文件格式: {ext}，仅支持 .xlsx/.xls/.pdf/.csv')

    if not parsed:
        raise HTTPException(400, '未能从文件中解析出有效报价数据')

    saved_quotes = []
    for item in parsed:
        q = SupplierQuote(
            project_id=project_id,
            supplier_company=item.get('supplier_company', ''),
            contact_name=item.get('contact_name', ''),
            phone=item.get('phone', ''),
            email=item.get('email', ''),
            product_service_detail=item.get('product_service_detail', ''),
            price=item.get('price'),
            currency=item.get('currency', 'CNY'),
            category=item.get('category', ''),
        )
        db.add(q)
        saved_quotes.append(item)

    db.commit()
    update_price_references(db)

    return {
        'ok': True,
        'count': len(saved_quotes),
        'quotes': saved_quotes,
    }


def parse_excel_quote(content: bytes) -> List[dict]:
    """解析 Excel 报价文件 — 智能识别表头并提取报价数据"""
    import openpyxl
    wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
    results = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue

        # ── 1. 智能定位表头（前10行中找含关键词最多的行作为表头）──
        header_row_idx = 0
        best_score = 0
        for i in range(min(10, len(rows))):
            candidate = [str(c).strip().lower() if c is not None else '' for c in rows[i]]
            col_map_test = map_columns(candidate)
            score = len(col_map_test)
            if score > best_score:
                best_score = score
                header_row_idx = i
                header = candidate
                col_map = col_map_test

        if best_score == 0:
            continue  # 无法识别任何列

        # ── 2. 提取数据行 ──
        for row in rows[header_row_idx + 1:]:
            # 跳过全空行
            if not any(c is not None and str(c).strip() for c in row):
                continue

            item = extract_from_row_enhanced(row, col_map)

            # 跳过汇总行（含"合计"/"总计"等关键词）
            all_text = ' '.join(str(c) for c in row if c).lower()
            if any(kw in all_text for kw in ['合计', '总计', 'total', '小计', '备注']):
                if not item.get('product_service_detail') and not item.get('price'):
                    continue

            if item.get('product_service_detail') or item.get('price') is not None:
                results.append(item)

    return results


def parse_csv_quote(content: bytes) -> List[dict]:
    """解析 CSV 报价文件"""
    import io, csv
    content_str = content.decode('utf-8-sig')
    reader = csv.reader(io.StringIO(content_str))
    rows = list(reader)
    if not rows:
        return []

    header = [c.strip().lower() if c else '' for c in rows[0]]
    col_map = map_columns(header)
    results = []

    for row in rows[1:]:
        if not any(row):
            continue
        item = extract_from_row(row, col_map)
        if item.get('product_service_detail') or item.get('price'):
            results.append(item)

    return results


def parse_pdf_quote(content: bytes) -> List[dict]:
    """解析 PDF 报价文件"""
    import fitz
    doc = fitz.open(stream=content, filetype='pdf')
    full_text = ''
    for page in doc:
        full_text += page.get_text() + '\n'

    results = []
    # Try to extract tabular data from the text
    lines = [l.strip() for l in full_text.split('\n') if l.strip()]

    # Heuristic: try to find supplier info first
    supplier_company = ''
    contact_name = ''
    phone = ''
    email = ''

    for line in lines:
        # Look for supplier company name patterns
        if any(kw in line for kw in ['公司', '供应商', 'Supplier', 'Company']):
            supplier_company = line.split('：')[-1].split(':')[-1].strip() if supplier_company == '' else supplier_company
        # Email
        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', line)
        if email_match and not email:
            email = email_match.group()
        # Phone
        phone_match = re.search(r'1[3-9]\d{9}|\d{3,4}-?\d{7,8}', line)
        if phone_match and not phone:
            phone = phone_match.group()

    # Try to find price info
    for line in lines:
        # Look for currency indicators
        currency = 'CNY'
        if 'HKD' in line or 'HK$' in line or '港币' in line or '港元' in line:
            currency = 'HKD'
        elif 'MOP' in line or 'MOP$' in line or '澳门' in line:
            currency = 'MOP'
        elif '$' in line and 'US' in line:
            currency = 'USD'

        # Try to extract price (number with decimal)
        prices = re.findall(r'(?:¥|￥|RMB|CNY|HKD|MOP|USD|\$)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:元|万)?', line)
        prices_clean = []
        for p in prices:
            try:
                val = float(p.replace(',', ''))
                if val > 0:
                    prices_clean.append(val)
            except:
                pass

        if prices_clean:
            # Assume the largest number is the price, and preceding text is the product
            max_price = max(prices_clean) if len(prices_clean) == 1 else prices_clean[-1]
            product = re.sub(r'(?:¥|￥|RMB|CNY|HKD|MOP|USD|\$)?\s*\d[\d,.]*\s*(?:元|万)?', '', line).strip()
            if product and len(product) >= 2:
                results.append({
                    'supplier_company': supplier_company,
                    'contact_name': contact_name,
                    'phone': phone,
                    'email': email,
                    'product_service_detail': product[:500],
                    'price': max_price,
                    'currency': currency,
                    'category': '',
                })

    # If no structured results found, return single entry with full text
    if not results:
        results = [{
            'supplier_company': supplier_company,
            'contact_name': contact_name,
            'phone': phone,
            'email': email,
            'product_service_detail': full_text[:1000],
            'price': None,
            'currency': 'CNY',
            'category': '',
        }]

    return results


def map_columns(header: List[str]) -> dict:
    """Map column names to standard field names"""
    mapping = {
        'supplier_company': ['供应商', '公司', 'supplier', 'company', '厂商', '供货商', '卖方', '单位名称', '客户名称', '报价单位'],
        'contact_name': ['联系人', 'contact', '姓名', 'name', '对方联系人', '业务员', '销售'],
        'phone': ['电话', 'phone', 'tel', '手机', 'mobile', '联系电话', '联系方式', '传真'],
        'email': ['邮箱', 'email', 'mail', 'e-mail', '电子邮箱', '邮件'],
        'product_service_detail': [
            '产品', '服务', '描述', 'product', 'service', 'detail', 'description',
            '设备名称', '型号', '品名', '项目', '名称', '规格', '货物名称',
            '商品名称', '产品名称', '产品型号', '规格型号', '规格参数',
            '物料名称', '物料描述', '货品名称', '货物', '内容', '项目名称',
            '说明', 'item', 'model', 'part', '物料',
        ],
        'price': [
            '价格', '单价', '金额', 'price', 'amount', '报价', '总价', '小计',
            '含税单价', '不含税单价', '含税总价', '未税单价', '未税总价',
            '单价(元)', '合计金额', '金额(元)', '费用', '单价(含税)',
            '售价', '成本价', 'unit price', 'total', '小计金额',
        ],
        'currency': ['币种', '货币', 'currency', '单位', '币别'],
        'category': ['类别', '分类', 'category', 'type', '类型', '产品类别', '商品类别', '物料类别', '品类'],
    }

    result = {}
    for field, keywords in mapping.items():
        for i, h in enumerate(header):
            if any(kw in h for kw in keywords):
                result[field] = i
                break

    return result


def extract_from_row(row: tuple, col_map: dict) -> dict:
    """Extract fields from a row using column mapping (legacy)"""
    return extract_from_row_enhanced(row, col_map)


def extract_from_row_enhanced(row: tuple, col_map: dict) -> dict:
    """Enhanced extraction — handles Excel numeric types and multi-column detail"""
    item = {}
    for field, idx in col_map.items():
        if idx < len(row):
            val = row[idx]
            if val is None or (isinstance(val, str) and not val.strip()):
                continue
            if field == 'price':
                if isinstance(val, (int, float)):
                    item[field] = float(val)
                else:
                    try:
                        s = str(val).replace(',', '').replace('¥', '').replace('￥', '').replace(' ', '')
                        item[field] = float(s)
                    except ValueError:
                        item[field] = None
            elif field == 'product_service_detail':
                existing = item.get(field, '')
                s = str(val).strip()
                if existing and s and s != 'None':
                    item[field] = existing + ' ' + s
                else:
                    item[field] = s
            else:
                s = str(val).strip()
                if s and s != 'None':
                    item[field] = s

    item.setdefault('supplier_company', '')
    item.setdefault('contact_name', '')
    item.setdefault('phone', '')
    item.setdefault('email', '')
    item.setdefault('product_service_detail', '')
    item.setdefault('price', None)
    item.setdefault('currency', 'CNY')
    item.setdefault('category', '')
    return item


# ════════════════════════════════════════════════════════════
#  Helper
# ════════════════════════════════════════════════════════════

def parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val)[:10], '%Y-%m-%d').date()
    except:
        return None


def serialize(obj):
    """Convert SQLAlchemy object to dict"""
    if obj is None:
        return None
    d = {}
    for c in obj.__table__.columns:
        val = getattr(obj, c.name)
        if isinstance(val, (datetime, date)):
            val = val.isoformat() if isinstance(val, datetime) else str(val)
        d[c.name] = val
    return d


# ── Static Files ────────────────────────────────────────────
if os.path.exists(os.path.join(FRONTEND_DIR, 'css')):
    app.mount('/css', StaticFiles(directory=os.path.join(FRONTEND_DIR, 'css')), name='css')
if os.path.exists(os.path.join(FRONTEND_DIR, 'js')):
    app.mount('/js', StaticFiles(directory=os.path.join(FRONTEND_DIR, 'js')), name='js')


@app.get('/')
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
