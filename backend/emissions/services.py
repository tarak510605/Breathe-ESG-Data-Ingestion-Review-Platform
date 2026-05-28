"""Emissions service layer."""
from emissions.models import NormalizedEmissionRecord


class ReviewQueueService:
    """Service for managing review queue."""
    
    @staticmethod
    def get_pending_records(organization_id, limit=50, offset=0):
        """Get pending review records."""
        queryset = NormalizedEmissionRecord.objects.filter(
            organization_id=organization_id,
            status='pending_review',
            review_decision='pending'
        ).order_by('-created_at')
        
        return queryset[offset:offset + limit]
    
    @staticmethod
    def get_record_by_id(organization_id, record_id):
        """Get a specific record."""
        return NormalizedEmissionRecord.objects.filter(
            organization_id=organization_id,
            id=record_id
        ).first()
