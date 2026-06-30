"""
Project Tracker - Database Models
客户、项目、供应商报价、价格参考四张核心表
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, Text, create_engine
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(200), nullable=False, index=True)
    address = Column(String(500))
    contact_name = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    projects = relationship('Project', back_populates='customer', cascade='all, delete-orphan')


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False, index=True)
    description = Column(Text)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    quotation_date = Column(Date)  # 报价完成时间
    final_price = Column(Float)  # 出街价格
    final_price_notes = Column(Text)  # 出街价格备注
    final_margin = Column(Float)  # 出街毛利
    final_margin_notes = Column(Text)  # 出街毛利备注
    cost_price = Column(Float)  # 成本价格
    is_landed = Column(Boolean, default=False)  # 是否落地
    landed_date = Column(Date)  # 落地日期
    category = Column(String(200))  # 项目类别
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    customer = relationship('Customer', back_populates='projects')
    supplier_quotes = relationship('SupplierQuote', back_populates='project', cascade='all, delete-orphan')


class SupplierQuote(Base):
    __tablename__ = 'supplier_quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    supplier_company = Column(String(200), nullable=False)
    contact_name = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    product_service_detail = Column(Text)  # 产品/服务详细情况
    price = Column(Float)
    currency = Column(String(10), default='CNY')  # CNY/HKD/MOP
    category = Column(String(200))  # 产品/服务归类
    created_at = Column(DateTime, default=datetime.now)

    project = relationship('Project', back_populates='supplier_quotes')


class PriceReference(Base):
    __tablename__ = 'price_references'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(200), nullable=False, index=True)
    product_service_name = Column(String(500), nullable=False)
    model = Column(String(500))  # 设备型号
    avg_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    min_price_supplier = Column(String(500))  # 最低价供应商
    max_price_supplier = Column(String(500))  # 最高价供应商
    currency = Column(String(10), default='CNY')
    quote_count = Column(Integer, default=1)
    supplier_list = Column(Text)  # JSON array of supplier names
    latest_quote_date = Column(Date)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_db(db_path='data/tracker_v2.db'):
    """Initialize database and create all tables"""
    engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    return engine
