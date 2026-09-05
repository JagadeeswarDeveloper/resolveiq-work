"""Initialize API module."""

from fastapi import APIRouter

from .endpoints import complaints, dashboard, incidents, customers, system, knowledge, workflows

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(incidents.cluster_router, prefix="/clusters", tags=["Clusters"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

