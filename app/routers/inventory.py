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
from ..models.inventory_history import InventoryHistory as InventoryHistoryModel
from ..models.user import User as UserModel

# Import Skema Pydantic dengan alias
from ..schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    InventoryItemType as InventoryItemTypeSchema,
    InventoryStatus as InventoryStatusSchema,
)
from ..schemas.inventory_history import InventoryHistoryResponse

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


async def log_inventory_change(
    db: AsyncSession,
    item_id: int,
    action: str,
    user_id: int
):
    """
    Helper function untuk mencatat perubahan inventory ke history
    """
    try:
        from sqlalchemy import text

        # Use direct SQL INSERT to avoid session conflicts
        query = text("""
            INSERT INTO inventory_history (item_id, action, user_id, timestamp)
            VALUES (:item_id, :action, :user_id, NOW())
        """)

        await db.execute(query, {
            "item_id": item_id,
            "action": action,
            "user_id": user_id
        })
        await db.commit()  # Commit immediately to avoid conflicts

        logger.info(f"Logged inventory history: item_id={item_id}, action={action}, user_id={user_id}")
    except Exception as e:
        logger.error(f"Failed to log inventory history: {str(e)}")
        # Jangan raise exception agar tidak mengganggu flow utama


@router.post("/", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(item: InventoryItemCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_item = InventoryItemModel(**item.model_dump())
        db.add(db_item)
        await db.commit()

        # Log history
        action_text = f"Created item - SN: {db_item.serial_number}, Type ID: {db_item.item_type_id}, Location: {db_item.location or 'Not set'}"
        await log_inventory_change(db, db_item.id, action_text, user_id=1)  # TODO: Get actual user ID

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
        changes = []

        # Track changes before applying
        for key, value in update_data.items():
            old_value = getattr(db_item, key)
            if old_value != value:
                if key == 'status_id':
                    changes.append(f"Status changed from {old_value} to {value}")
                elif key == 'location':
                    changes.append(f"Location changed from '{old_value}' to '{value}'")
                elif key == 'item_type_id':
                    changes.append(f"Type changed from {old_value} to {value}")
                else:
                    changes.append(f"{key} changed from '{old_value}' to '{value}'")

        # Apply updates
        for key, value in update_data.items():
            setattr(db_item, key, value)

        await db.commit()

        # Log history if there are changes
        if changes:
            action_text = f"Updated item - SN: {db_item.serial_number}, Changes: {', '.join(changes)}"
            await log_inventory_change(db, db_item.id, action_text, user_id=1)  # TODO: Get actual user ID

        # Refresh relationships for response
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

        # Save info for history before deleting
        item_info = f"SN: {db_item.serial_number}, Type ID: {db_item.item_type_id}, Location: {db_item.location or 'Not set'}"

        # Log history before delete
        action_text = f"Deleted item - {item_info}"
        await log_inventory_change(db, item_id, action_text, user_id=1)  # TODO: Get actual user ID

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


@router.get("/{item_id}/history", response_model=List[InventoryHistoryResponse])
async def get_inventory_history(item_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mendapatkan history perubahan untuk inventory item tertentu
    """
    try:
        # Cek apakah item ada
        item = await db.get(InventoryItemModel, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        # Query history dengan relasi user
        query = (
            select(InventoryHistoryModel)
            .options(selectinload(InventoryHistoryModel.user))
            .where(InventoryHistoryModel.item_id == item_id)
            .order_by(InventoryHistoryModel.timestamp.desc())
        )
        result = await db.execute(query)
        history_items = result.scalars().all()

        logger.info(f"Retrieved {len(history_items)} history items for inventory item {item_id}")
        return history_items

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving inventory history for item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory history: {str(e)}",
        )


@router.get("/history/all", response_model=List[dict])
async def get_all_inventory_history(db: AsyncSession = Depends(get_db)):
    """
    Mendapatkan semua history inventory dari semua item dengan informasi item
    """
    try:
        # Query all history dengan join ke item dan user
        query = (
            select(
                InventoryHistoryModel,
                InventoryItemModel.serial_number,
                InventoryItemModel.mac_address
            )
            .join(InventoryItemModel, InventoryHistoryModel.item_id == InventoryItemModel.id)
            .options(selectinload(InventoryHistoryModel.user))
            .order_by(InventoryHistoryModel.timestamp.desc())
        )
        result = await db.execute(query)
        history_rows = result.all()

        # Format response
        history_items = []
        for history_row in history_rows:
            history, serial_number, mac_address = history_row
            history_items.append({
                "id": history.id,
                "item_id": history.item_id,
                "action": history.action,
                "timestamp": history.timestamp,
                "serial_number": serial_number,
                "mac_address": mac_address,
                "user": {
                    "id": history.user.id if history.user else None,
                    "name": history.user.name if history.user else "System"
                }
            })

        logger.info(f"Retrieved {len(history_items)} total history items")
        return history_items

    except Exception as e:
        logger.error(f"Error retrieving all inventory history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory history: {str(e)}",
        )
