"""
SQLAlchemy ORM модели - отображение сущностей в БД
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean,
    Float, BigInteger, UniqueConstraint, Index as SQLIndex
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserModel(Base):
    """ORM модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    databases = relationship("DatabaseModel", back_populates="owner")
    query_logs = relationship("QueryLogModel", back_populates="user")
    backup_logs = relationship("BackupLogModel", back_populates="user")
    
    __table_args__ = (
        SQLIndex('idx_username', 'username'),
        SQLIndex('idx_email', 'email'),
    )


class DatabaseModel(Base):
    """ORM модель подключения к БД"""
    __tablename__ = "databases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=5432)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    database_name = Column(String(100), nullable=False)
    status = Column(String(20), default="disconnected")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # JSON-массив строк привилегий, например: ["CONNECT","USAGE","SELECT"]
    access_privileges = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_checked = Column(DateTime(timezone=True))
    
    # Relationships
    owner = relationship("UserModel", back_populates="databases")
    tables = relationship("TableModel", back_populates="database", cascade="all, delete-orphan")
    query_logs = relationship("QueryLogModel", back_populates="database")
    backup_logs = relationship("BackupLogModel", back_populates="database")
    
    __table_args__ = (
        SQLIndex("idx_owner_id", "owner_id"),
        UniqueConstraint(
            "owner_id",
            "host",
            "port",
            "database_name",
            name="unique_owner_host_port_database_name",
        ),
    )


class TableModel(Base):
    """ORM модель таблицы БД"""
    __tablename__ = "tables"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    row_count = Column(Integer, default=0)
    size_bytes = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    database = relationship("DatabaseModel", back_populates="tables")
    columns = relationship("ColumnModel", back_populates="table", cascade="all, delete-orphan")
    indexes = relationship("IndexModel", back_populates="table", cascade="all, delete-orphan")
    
    __table_args__ = (
        SQLIndex('ix_tables_database_id', 'database_id'),
        UniqueConstraint('database_id', 'name', name='unique_database_table_name'),
    )


class ColumnModel(Base):
    """ORM модель колонки БД"""
    __tablename__ = "columns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    data_type = Column(String(50), nullable=False)
    is_nullable = Column(Boolean, default=True)
    is_primary_key = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    default_value = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    table = relationship("TableModel", back_populates="columns")
    
    __table_args__ = (
        SQLIndex('ix_columns_table_id', 'table_id'),
    )


class IndexModel(Base):
    """ORM модель индекса БД"""
    __tablename__ = "indexes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    columns = Column(Text, nullable=False)  # JSON сохраняем как текст
    is_unique = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    table = relationship("TableModel", back_populates="indexes")
    
    __table_args__ = (
        SQLIndex('ix_indexes_table_id', 'table_id'),
    )


class QueryLogModel(Base):
    """ORM модель логирования запросов"""
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    status = Column(String(20), default="success")
    error_message = Column(Text)
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("UserModel", back_populates="query_logs")
    database = relationship("DatabaseModel", back_populates="query_logs")
    
    __table_args__ = (
        SQLIndex('ix_query_logs_user_id', 'user_id'),
        SQLIndex('ix_query_logs_database_id', 'database_id'),
        SQLIndex('ix_query_logs_created_at', 'created_at'),
    )


class BackupLogModel(Base):
    """ORM модель логирования резервных копий"""
    __tablename__ = "backup_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    backup_name = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, default=0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    database = relationship("DatabaseModel", back_populates="backup_logs")
    user = relationship("UserModel", back_populates="backup_logs")
    
    __table_args__ = (
        SQLIndex('ix_backup_logs_database_id', 'database_id'),
        SQLIndex('ix_backup_logs_user_id', 'user_id'),
        SQLIndex('ix_backup_logs_status', 'status'),
    )
