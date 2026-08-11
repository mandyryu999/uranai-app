from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    name_kana: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=255)
    line_name: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    name_kana: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=255)
    line_name: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class ClientRead(ClientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class BirthProfileCreate(BaseModel):
    birth_date: date
    birth_time: time | None = None
    birth_time_unknown: bool = False
    birthplace_prefecture: str | None = Field(default=None, max_length=100)
    birthplace_city: str | None = Field(default=None, max_length=120)
    birthplace_detail: str | None = Field(default=None, max_length=255)
    timezone: str = Field(default="Asia/Tokyo", min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_birth_time(self):
        if self.birth_time_unknown:
            self.birth_time = None
        return self


class BirthProfileUpdate(BaseModel):
    birth_date: date | None = None
    birth_time: time | None = None
    birth_time_unknown: bool | None = None
    birthplace_prefecture: str | None = Field(default=None, max_length=100)
    birthplace_city: str | None = Field(default=None, max_length=120)
    birthplace_detail: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)


class BirthProfileRead(BirthProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime


class SanmeigakuChartBase(BaseModel):
    year_pillar: str | None = Field(default=None, max_length=20)
    month_pillar: str | None = Field(default=None, max_length=20)
    day_pillar: str | None = Field(default=None, max_length=20)
    center_star: str | None = Field(default=None, max_length=40)
    north_star: str | None = Field(default=None, max_length=40)
    east_star: str | None = Field(default=None, max_length=40)
    south_star: str | None = Field(default=None, max_length=40)
    west_star: str | None = Field(default=None, max_length=40)
    early_star: str | None = Field(default=None, max_length=40)
    middle_star: str | None = Field(default=None, max_length=40)
    late_star: str | None = Field(default=None, max_length=40)
    tenchusatsu: str | None = Field(default=None, max_length=40)
    calculation_source: str | None = Field(default=None, max_length=120)
    calculation_version: str | None = Field(default=None, max_length=40)
    notes: str | None = None


class SanmeigakuChartCreate(SanmeigakuChartBase):
    pass


class SanmeigakuChartUpdate(SanmeigakuChartBase):
    pass


class SanmeigakuChartRead(SanmeigakuChartBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime


class ReadingCreate(BaseModel):
    reading_at: datetime | None = None
    theme: str | None = Field(default=None, max_length=160)
    consultation: str | None = None
    methods: str | None = Field(default=None, max_length=255)
    result: str | None = None
    advice: str | None = None
    follow_up: str | None = None
    private_notes: str | None = None


class ReadingUpdate(BaseModel):
    reading_at: datetime | None = None
    theme: str | None = Field(default=None, max_length=160)
    consultation: str | None = None
    methods: str | None = Field(default=None, max_length=255)
    result: str | None = None
    advice: str | None = None
    follow_up: str | None = None
    private_notes: str | None = None


class ReadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    reading_at: datetime
    theme: str | None
    consultation: str | None
    methods: str | None
    result: str | None
    advice: str | None
    follow_up: str | None
    private_notes: str | None
    created_at: datetime
    updated_at: datetime


class AIReadingRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    reading_limit: int = Field(default=10, ge=1, le=100)
    model: str | None = Field(default=None, max_length=80)
