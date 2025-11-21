from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import logging
import re

from ..database import get_db

# Import Model dengan alias
from ..models.inventory_item import InventoryItem as InventoryItemModel
from ..models.inventory_item_type import InventoryItemType as InventoryItemTypeModel
from ..models.inventory_status import InventoryStatus as InventoryStatusModel

# Import Skema Pydantic dengan alias
from ..schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    InventoryItemType as InventoryItemTypeSchema,
    InventoryStatus as InventoryStatusSchema,
)

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(item: InventoryItemCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_item = InventoryItemModel(**item.model_dump())
        db.add(db_item)
        await db.commit()
        # Muat relasi secara eksplisit setelah commit
        await db.refresh(db_item, ["item_type", "status"])
        logger.info(f"Created inventory item with ID: {db_item.id}")
        return db_item
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating inventory item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inventory item: {str(e)}",
        )


@router.get("/", response_model=List[InventoryItemResponse])
async def get_inventory_items(db: AsyncSession = Depends(get_db)):
    try:
        query = (
            select(InventoryItemModel)
            .options(
                selectinload(InventoryItemModel.item_type),
                selectinload(InventoryItemModel.status),
            )
            .order_by(InventoryItemModel.id)
        )
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error retrieving inventory items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory items: {str(e)}",
        )


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(item_id: int, item_update: InventoryItemUpdate, db: AsyncSession = Depends(get_db)):
    try:
        db_item = await db.get(InventoryItemModel, item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")

        update_data = item_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)

        await db.commit()
        await db.refresh(db_item, ["item_type", "status"])
        logger.info(f"Updated inventory item with ID: {db_item.id}")
        return db_item
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating inventory item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update inventory item: {str(e)}",
        )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        db_item = await db.get(InventoryItemModel, item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        await db.delete(db_item)
        await db.commit()
        logger.info(f"Deleted inventory item with ID: {item_id}")
        return
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting inventory item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete inventory item: {str(e)}",
        )


# Helper endpoints untuk dropdown
@router.get("/types", response_model=List[InventoryItemTypeSchema])
async def get_item_types(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(InventoryItemTypeModel).order_by(InventoryItemTypeModel.name))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error retrieving item types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve item types: {str(e)}",
        )


@router.get("/statuses", response_model=List[InventoryStatusSchema])
async def get_statuses(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(InventoryStatusModel).order_by(InventoryStatusModel.name))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error retrieving statuses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statuses: {str(e)}",
        )


@router.post("/validate-barcode")
async def validate_barcode(barcode_data: dict, db: AsyncSession = Depends(get_db)):
    """
    Validasi dan format barcode data untuk Serial Number atau MAC Address
    """
    try:
        barcode_text = barcode_data.get("barcode", "").strip()
        barcode_type = barcode_data.get("type", "serial")  # 'serial' atau 'mac'

        if not barcode_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Barcode text cannot be empty"
            )

        result = {
            "original": barcode_text,
            "type": barcode_type,
            "valid": False,
            "formatted": None,
            "message": ""
        }

        if barcode_type == "mac":
            # Clean MAC address
            cleaned = re.sub(r'[^a-fA-F0-9]', '', barcode_text)

            if len(cleaned) != 12:
                result["message"] = "MAC Address harus terdiri dari 12 karakter hexadesimal"
                return result

            # Validate hex characters
            if not all(c in "0123456789ABCDEF" for c in cleaned.upper()):
                result["message"] = "MAC Address hanya boleh mengandung karakter hexadesimal (0-9, A-F)"
                return result

            # Format as AA:BB:CC:DD:EE:FF
            formatted_mac = ":".join([cleaned[i:i+2] for i in range(0, 12, 2)]).upper()

            # Check for duplicates
            existing = await db.execute(
                select(InventoryItemModel).where(InventoryItemModel.mac_address == formatted_mac)
            )
            if existing.scalar():
                result["message"] = "MAC Address sudah terdaftar dalam sistem"
                return result

            result["valid"] = True
            result["formatted"] = formatted_mac
            result["message"] = "MAC Address valid"

        elif barcode_type == "serial":
            # Clean serial number
            cleaned = re.sub(r'[^A-Za-z0-9\-_]', '', barcode_text).upper()

            if not cleaned:
                result["message"] = "Serial Number tidak valid"
                return result

            if len(cleaned) > 100:
                result["message"] = "Serial Number terlalu panjang (maksimal 100 karakter)"
                return result

            # Check for duplicates
            existing = await db.execute(
                select(InventoryItemModel).where(InventoryItemModel.serial_number == cleaned)
            )
            if existing.scalar():
                result["message"] = "Serial Number sudah terdaftar dalam sistem"
                return result

            result["valid"] = True
            result["formatted"] = cleaned
            result["message"] = "Serial Number valid"

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating barcode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate barcode: {str(e)}",
        )
