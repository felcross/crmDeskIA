from app.repositories.base import BaseRepository
from app.repositories.captured_lead_repo import CapturedLeadRepository
from app.repositories.deal_repo import DealRepository
from app.repositories.lead_repo import LeadRepository
from app.repositories.user_repo import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "CapturedLeadRepository",
    "LeadRepository",
    "DealRepository",
]
