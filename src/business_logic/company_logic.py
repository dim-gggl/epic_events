from src.data_access.repository import company_repository
from src.data_access.config import Session
from src.crm.models import Company
from src.auth.permissions import has_permission
from typing import List, Optional
from sqlalchemy.orm import joinedload

class CompanyLogic:
    def create_company(self, access_token: str, company_data: dict) -> Company:
        """
        Create a new company.
        Only commercial and management roles can create companies.
        """
        if not has_permission(access_token, "company:create"):
            raise PermissionError("You don't have permission to create companies.")
        
        with Session() as session:
            company = company_repository.create(company_data, session)
            session.commit()
            session.refresh(company)
            return company

    def get_companies(self, access_token: str) -> List[Company]:
        """
        Get all companies.
        Only commercial and management roles can list companies.
        """
        if not has_permission(access_token, "company:list"):
            raise PermissionError("You don't have permission to list companies.")
        
        with Session() as session:
            return company_repository.get_all(session)

    def get_company_by_id(self, company_id: int) -> Optional[Company]:
        """
        Get a company by its ID.
        """
        with Session() as session:
            return session.query(Company).options(joinedload(Company.clients)).filter(Company.id == company_id).first()

    def update_company(self, access_token: str, company_id: int, company_data: dict) -> Optional[Company]:
        """
        Update a company.
        Only management role can update companies.
        """
        if not has_permission(access_token, "company:update"):
            raise PermissionError("You don't have permission to update companies.")
        
        with Session() as session:
            company = company_repository.get_by_id(company_id, session)
            if not company:
                return None
            
            updated_company = company_repository.update(company_id, company_data, session)
            session.commit()
            if updated_company:
                session.refresh(updated_company)
            return updated_company

    def delete_company(self, access_token: str, company_id: int) -> bool:
        """
        Delete a company.
        Only management role can delete companies.
        Business rule: cannot delete company with associated clients.
        """
        if not has_permission(access_token, "company:delete"):
            raise PermissionError("You don't have permission to delete companies.")
        
        with Session() as session:
            company = company_repository.get_by_id(company_id, session)
            if not company:
                return False

            # Business rule: cannot delete company with associated clients
            if company.clients:
                raise ValueError("Cannot delete a company with associated clients.")

            deleted = company_repository.delete(company_id, session)
            if deleted:
                session.commit()
            return deleted

company_logic = CompanyLogic()
