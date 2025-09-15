
from sqlalchemy.orm import joinedload

from src.auth.permissions import login_required, require_permission
from src.crm.models import Company
from src.data_access.config import Session
from src.data_access.repository import company_repository


class CompanyLogic:
    @require_permission("company:create")
    def create_company(self, access_token: str, company_data: dict) -> Company:
        """
        Create a new company.
        Only commercial and management roles can create companies.
        """
        with Session() as session:
            company = company_repository.create(company_data, session)
            session.commit()
            session.refresh(company)
            return company


    @login_required
    def get_companies(self, access_token: str) -> list[Company]:
        """
        Get all companies.
        Only commercial and management roles can list companies.
        """
        with Session() as session:
            return company_repository.get_all(session)

    @require_permission("company:view")
    def get_company_by_id(self, access_token: str, company_id: int) -> Company | None:
        """
        Get a company by its ID.
        Requires permission: company:view
        """
        with Session() as session:
            return (
                session
                .query(Company)
                .options(joinedload(Company.clients))
                .filter(Company.id == company_id)
                .first()
            )

    @require_permission("company:update")
    def update_company(self,
                       access_token: str,
                       company_id: int,
                       company_data: dict) -> Company | None:
        """
        Update a company.
        Only management role can update companies.
        """
        with Session() as session:
            company = company_repository.get_by_id(company_id, session)
            if not company:
                return None

            updated_company = company_repository.update(company_id, company_data, session)
            session.commit()
            if updated_company:
                session.refresh(updated_company)
            return updated_company

    @require_permission("company:delete")
    def delete_company(self, access_token: str, company_id: int) -> bool:
        """
        Delete a company.
        Only management role can delete companies.
        Business rule: cannot delete company with associated clients.
        """
        with Session() as session:
            company = company_repository.get_by_id(company_id, session)
            if not company:
                return

            if company.clients:
                raise ValueError("Cannot delete a company with associated clients.")

            deleted = company_repository.delete(company_id, session)
            if deleted:
                session.commit()
            return deleted

company_logic = CompanyLogic()
