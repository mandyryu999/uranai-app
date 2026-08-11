from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    name_kana: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    line_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    birth_profile: Mapped["BirthProfile | None"] = relationship(
        back_populates="client", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    sanmeigaku_chart: Mapped["SanmeigakuChart | None"] = relationship(
        back_populates="client", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    readings: Mapped[list["Reading"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", passive_deletes=True
    )


class BirthProfile(Base):
    __tablename__ = "birth_profiles"
    __table_args__ = (UniqueConstraint("client_id", name="uq_birth_profiles_client_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    birth_time_unknown: Mapped[bool] = mapped_column(default=False, nullable=False)
    birthplace_prefecture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    birthplace_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    birthplace_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tokyo", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    client: Mapped[Client] = relationship(back_populates="birth_profile")


class SanmeigakuChart(Base):
    __tablename__ = "sanmeigaku_charts"
    __table_args__ = (UniqueConstraint("client_id", name="uq_sanmeigaku_charts_client_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    year_pillar: Mapped[str | None] = mapped_column(String(20), nullable=True)
    month_pillar: Mapped[str | None] = mapped_column(String(20), nullable=True)
    day_pillar: Mapped[str | None] = mapped_column(String(20), nullable=True)
    center_star: Mapped[str | None] = mapped_column(String(40), nullable=True)
    north_star: Mapped[str | None] = mapped_column(String(40), nullable=True)
    east_star: Mapped[str | None] = mapped_column(String(40), nullable=True)
    south_star: Mapped[str | None] = mapped_column(String(40), nullable=True)
    west_star: Mapped[str | None] = mapped_column(String(40), nullable=True)
    early_star: Mapped[str | None] = mapped_column(String(40), nullable=True)
    middle_star: Mapped[str | None] = mapped_column(String(40), nullable=True)
    late_star: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tenchusatsu: Mapped[str | None] = mapped_column(String(40), nullable=True)
    calculation_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    calculation_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    client: Mapped[Client] = relationship(back_populates="sanmeigaku_chart")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    reading_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    theme: Mapped[str | None] = mapped_column(String(160), nullable=True)
    consultation: Mapped[str | None] = mapped_column(Text, nullable=True)
    methods: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    client: Mapped[Client] = relationship(back_populates="readings")
