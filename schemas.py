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


class SanmeigakuChartCreate(BaseModel):
    year_pillar: str = Field(min_length=2, max_length=10)
    month_pillar: str = Field(min_length=2, max_length=10)
    day_pillar: str = Field(min_length=2, max_length=10)
    day_stem: str = Field(min_length=1, max_length=4)
    tenchusatsu: str | None = Field(default=None, max_length=20)
    central_star: str | None = Field(default=None, max_length=20)
    north_star: str | None = Field(default=None, max_length=20)
    east_star: str | None = Field(default=None, max_length=20)
    south_star: str | None = Field(default=None, max_length=20)
    west_star: str | None = Field(default=None, max_length=20)
    childhood_star: str | None = Field(default=None, max_length=20)
    middle_age_star: str | None = Field(default=None, max_length=20)
    later_life_star: str | None = Field(default=None, max_length=20)
    source: str = Field(default="manual", min_length=1, max_length=30)
    notes: str | None = None


class SanmeigakuChartUpdate(BaseModel):
    year_pillar: str | None = Field(default=None, min_length=2, max_length=10)
    month_pillar: str | None = Field(default=None, min_length=2, max_length=10)
    day_pillar: str | None = Field(default=None, min_length=2, max_length=10)
    day_stem: str | None = Field(default=None, min_length=1, max_length=4)
    tenchusatsu: str | None = Field(default=None, max_length=20)
    central_star: str | None = Field(default=None, max_length=20)
    north_star: str | None = Field(default=None, max_length=20)
    east_star: str | None = Field(default=None, max_length=20)
    south_star: str | None = Field(default=None, max_length=20)
    west_star: str | None = Field(default=None, max_length=20)
    childhood_star: str | None = Field(default=None, max_length=20)
    middle_age_star: str | None = Field(default=None, max_length=20)
    later_life_star: str | None = Field(default=None, max_length=20)
    source: str | None = Field(default=None, min_length=1, max_length=30)
    notes: str | None = None


class SanmeigakuChartRead(SanmeigakuChartCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime
