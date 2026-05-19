"""PostgreSQL 접속 설정 (D44)."""
import os
from dataclasses import dataclass


@dataclass
class DBConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DBConfig":
        return cls(
            host=os.getenv("AWT_DB_HOST", "localhost"),
            port=int(os.getenv("AWT_DB_PORT", "5432")),
            dbname=os.getenv("AWT_DB_NAME", "awt"),
            user=os.getenv("AWT_DB_USER", "awt_user"),
            password=os.getenv("AWT_DB_PASSWORD", ""),
        )

    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.dbname} "
            f"user={self.user} password={self.password}"
        )
