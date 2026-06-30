#!/usr/bin/env python
"""生成导入模板 Excel 文件"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def create_template(path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "报价导入模板"

    # 表头
    headers = [
        "供应商公司", "供应商联系人", "供应商电话", "供应商邮箱",
        "产品/服务名称", "设备型号", "数量", "单位",
        "单价", "币种", "产品类别", "品牌/备注"
    ]

    # 样式
    header_font = Font(name="Microsoft YaHei", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="185FA5", end_color="185FA5", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )
    data_font = Font(name="Microsoft YaHei", size=11)

    # 写入表头
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # 示例数据
    examples = [
        ["PROMISE COMPANY LIMITED", "Che Hoi Lei", "+853 28261055", "info@promise.com.mo",
         "紧急呼叫系统网关 Telligence Station Gateway", "NGGTWY2-HNGGWPWR-AK", 3, "unit",
         48220, "MOP", "呼叫/报警系统", "Ascom"],
        ["海康威视", "张三", "13800138000", "zhang@hikvision.com",
         "泊车识别摄像机 DS-TCP440-B", "DS-TCP440-B", 81, "unit",
         1810, "MOP", "安防摄像头", "Hikvision / 大华可选"],
        ["", "", "", "",
         "智能停车场管理终端机 DS-TPM400-FP", "DS-TPM400-FP", 3, "unit",
         10760, "MOP", "停车系统", ""],
    ]

    # 类别下拉选项
    categories = [
        "安防摄像头", "门禁系统", "网络设备", "呼叫/报警系统",
        "停车系统", "软件/服务器", "显示设备", "机柜/配件",
        "线缆/管材", "电源设备", "广播/音响", "对讲系统", "其他设备"
    ]

    # 币种下拉选项
    currencies = ["CNY", "HKD", "MOP"]

    # 写入示例
    for r, row_data in enumerate(examples, 2):
        for c, val in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.font = data_font
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = thin_border

    # 列宽
    col_widths = [30, 15, 18, 28, 45, 28, 8, 8, 15, 8, 18, 30]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # 数据验证：币种
    curr_val = openpyxl.worksheet.datavalidation.DataValidation(
        type="list", formula1=f'"{",".join(currencies)}"', allow_blank=True
    )
    curr_val.error = "请选择 CNY / HKD / MOP"
    curr_val.errorTitle = "无效币种"
    ws.add_data_validation(curr_val)
    curr_val.add(f'J2:J1000')

    # 数据验证：类别
    cat_val = openpyxl.worksheet.datavalidation.DataValidation(
        type="list", formula1=f'"{",".join(categories)}"', allow_blank=True
    )
    cat_val.error = "请从下拉列表选择产品类别"
    cat_val.errorTitle = "无效类别"
    ws.add_data_validation(cat_val)
    cat_val.add(f'K2:K1000')

    # 冻结首行
    ws.freeze_panes = "A2"

    # 自动筛选
    ws.auto_filter.ref = f"A1:L{len(examples) + 10}"

    wb.save(path)
    print(f"模板已生成: {path}")

if __name__ == '__main__':
    import sys, os
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'template', 'import_template.xlsx')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    create_template(out)
