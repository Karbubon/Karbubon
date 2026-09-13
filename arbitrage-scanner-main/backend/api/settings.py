from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database import get_db
from ..models import UserSetting
from ..schemas import SettingResponse, SettingUpdate, SettingsBatchUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=List[SettingResponse])
async def get_all_settings(db: Session = Depends(get_db)):
    """Получить все настройки"""
    settings = db.query(UserSetting).all()
    return settings


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(key: str, db: Session = Depends(get_db)):
    """Получить настройку по ключу"""
    setting = db.query(UserSetting).filter(UserSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return setting


@router.put("/{key}", response_model=SettingResponse)
async def update_setting_put(
    key: str, update: SettingUpdate, db: Session = Depends(get_db)
):
    """Обновить настройку (PUT метод)"""
    setting = db.query(UserSetting).filter(UserSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    setting.value = update.value
    db.commit()
    db.refresh(setting)

    return setting


@router.post("/{key}", response_model=SettingResponse)
async def update_setting_post(
    key: str, update: SettingUpdate, db: Session = Depends(get_db)
):
    """Обновить настройку (POST метод)"""
    setting = db.query(UserSetting).filter(UserSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    setting.value = update.value
    db.commit()
    db.refresh(setting)

    return setting


@router.post("/batch", response_model=Dict[str, Any])
async def update_settings_batch(
    update: SettingsBatchUpdate, db: Session = Depends(get_db)
):
    """Массовое обновление настроек"""
    updated = []
    errors = []

    for key, value in update.settings.items():
        setting = db.query(UserSetting).filter(UserSetting.key == key).first()
        if setting:
            setting.value = value
            updated.append(key)
        else:
            errors.append(key)

    db.commit()

    return {
        "updated": updated,
        "errors": errors,
        "message": f"Updated {len(updated)} settings, {len(errors)} errors",
    }
