"""Category service."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryTreeNode


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CategoryRepository(session)

    async def list_tree(self, user_id: UUID) -> list[CategoryTreeNode]:
        categories = await self.repo.list_for_user(user_id)
        nodes = {c.id: CategoryTreeNode.model_validate(c) for c in categories}
        roots: list[CategoryTreeNode] = []
        for c in categories:
            node = nodes[c.id]
            if c.parent_id is not None and c.parent_id in nodes:
                nodes[c.parent_id].children.append(node)
            else:
                roots.append(node)
        return roots

    async def create(
        self, *, user_id: UUID, name: str, parent_id: UUID | None, kind: str
    ) -> Category:
        if parent_id is not None:
            parent = await self.repo.get_for_user(parent_id, user_id)
            if parent is None:
                raise NotFoundError("Parent category not found.")
            if parent.parent_id is not None:
                raise ConflictError("Subcategories cannot have their own subcategories.")
        category = await self.repo.create(
            user_id=user_id, name=name, parent_id=parent_id, kind=kind
        )
        await self.session.commit()
        return category

    async def update(
        self, *, category_id: UUID, user_id: UUID, name: str | None, is_archived: bool | None
    ) -> Category:
        category = await self.repo.get_owned(category_id, user_id)
        if category is None:
            # Distinguish "not found" from "system default (not editable)".
            visible = await self.repo.get_for_user(category_id, user_id)
            if visible is not None and visible.user_id is None:
                raise ForbiddenError("System default categories cannot be modified.")
            raise NotFoundError("Category not found.")
        if name is not None:
            category.name = name
        if is_archived is not None:
            category.is_archived = is_archived
        await self.session.commit()
        return category

    async def delete(self, *, category_id: UUID, user_id: UUID) -> None:
        category = await self.repo.get_owned(category_id, user_id)
        if category is None:
            visible = await self.repo.get_for_user(category_id, user_id)
            if visible is not None and visible.user_id is None:
                raise ForbiddenError("System default categories cannot be deleted.")
            raise NotFoundError("Category not found.")
        if await self.repo.has_expenses(category_id):
            # Referenced by expenses → archive instead of hard delete.
            category.is_archived = True
        else:
            await self.session.delete(category)
        await self.session.commit()
