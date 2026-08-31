# Authorization — Route-Level RBAC

> Full RBAC documentation is in [`RBAC.md`](./RBAC.md).

## Quick Reference

### require_role Dependency

```python
# app/core/dependencies.py
async def require_role(allowed_roles: list[UserRole]):
    async def inner(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        user = await get_current_user(token, db)
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return inner
```

### Role Assignment Per Route

```python
# Example: organizations.py router
@router.delete("/{id}", dependencies=[Depends(require_role([UserRole.ADMIN]))])
async def delete_organization(...): ...

@router.get("/", dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def list_organizations(...): ...
```

All `DELETE` and admin-only operations require `UserRole.ADMIN`.  
All read endpoints accept both `ADMIN` and `ANALYST`.
