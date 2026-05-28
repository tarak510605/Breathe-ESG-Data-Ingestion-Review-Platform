from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from emissions.models import NormalizedEmissionRecord, AnomalyFlag
from emissions.serializers import (
    NormalizedEmissionRecordListSerializer,
    NormalizedEmissionRecordDetailSerializer,
    NormalizedEmissionRecordEditSerializer,
    NormalizedEmissionRecordApproveSerializer,
    NormalizedEmissionRecordRejectSerializer,
    AnomalyFlagSerializer
)
from emissions.services import ReviewQueueService
from audit.services import AuditService
from breathe.permissions import IsAuthenticatedAndSetOrganization


class NormalizedEmissionRecordViewSet(viewsets.ModelViewSet):
    """
    Normalized emission records - main review interface.
    """
    permission_classes = [IsAuthenticatedAndSetOrganization]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NormalizedEmissionRecordDetailSerializer
        elif self.action in ['edit', 'partial_update']:
            return NormalizedEmissionRecordEditSerializer
        elif self.action == 'approve':
            return NormalizedEmissionRecordApproveSerializer
        elif self.action == 'reject':
            return NormalizedEmissionRecordRejectSerializer
        return NormalizedEmissionRecordListSerializer
    
    def get_queryset(self):
        if hasattr(self.request, 'organization') and self.request.organization:
            queryset = NormalizedEmissionRecord.objects.filter(
                organization=self.request.organization
            )
            
            # Filter by status
            status_param = self.request.query_params.get('status')
            if status_param:
                queryset = queryset.filter(status=status_param)
            
            # Filter by emission category
            category = self.request.query_params.get('emission_category')
            if category:
                queryset = queryset.filter(emission_category=category)
            
            # Filter by review decision
            review_decision = self.request.query_params.get('review_decision')
            if review_decision:
                queryset = queryset.filter(review_decision=review_decision)
            
            # Filter by period
            period_start = self.request.query_params.get('period_start')
            if period_start:
                queryset = queryset.filter(period_start__gte=period_start)
            
            period_end = self.request.query_params.get('period_end')
            if period_end:
                queryset = queryset.filter(period_end__lte=period_end)
            
            return queryset.order_by('-created_at')
        
        return NormalizedEmissionRecord.objects.none()
    
    @action(detail=False, methods=['get'])
    def review_queue(self, request):
        """Get pending records for review."""
        queryset = self.get_queryset().filter(
            status='pending_review',
            review_decision='pending'
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a record."""
        record = self.get_object()
        
        if record.is_locked:
            return Response(
                {'error': 'Record is locked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = NormalizedEmissionRecordApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        comment = serializer.validated_data.get('comment', '')
        
        # Update record
        record.status = 'approved'
        record.review_decision = 'approved'
        record.reviewed_by = request.user
        record.review_timestamp = __import__('django.utils.timezone', fromlist=['now']).now()
        record.review_comment = comment
        record.is_locked = True
        record.save()
        
        # Log action
        audit_service = AuditService()
        audit_service.log_action(
            user=request.user,
            record_id=str(record.id),
            record_type='NormalizedEmissionRecord',
            action='approved',
            change_reason=comment
        )
        
        serializer = NormalizedEmissionRecordDetailSerializer(record)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a record."""
        record = self.get_object()
        
        if record.is_locked:
            return Response(
                {'error': 'Record is locked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = NormalizedEmissionRecordRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reason = serializer.validated_data['reason']
        
        # Update record
        record.status = 'rejected'
        record.review_decision = 'rejected'
        record.reviewed_by = request.user
        record.review_timestamp = __import__('django.utils.timezone', fromlist=['now']).now()
        record.review_comment = reason
        record.save()
        
        # Log action
        audit_service = AuditService()
        audit_service.log_action(
            user=request.user,
            record_id=str(record.id),
            record_type='NormalizedEmissionRecord',
            action='rejected',
            change_reason=reason
        )
        
        serializer = NormalizedEmissionRecordDetailSerializer(record)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def audit_trail(self, request, pk=None):
        """Get audit trail for a record."""
        from audit.models import AuditLog
        from audit.serializers import AuditLogSerializer
        
        record = self.get_object()
        logs = AuditLog.objects.filter(
            record_id=str(record.id),
            record_type='NormalizedEmissionRecord',
            organization=request.organization
        ).order_by('-created_at')
        
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)


class AnomalyFlagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view of anomaly flags.
    """
    serializer_class = AnomalyFlagSerializer
    permission_classes = [IsAuthenticatedAndSetOrganization]
    
    def get_queryset(self):
        if hasattr(self.request, 'organization') and self.request.organization:
            return AnomalyFlag.objects.filter(
                organization=self.request.organization
            ).order_by('-created_at')
        return AnomalyFlag.objects.none()
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get unresolved anomalies."""
        queryset = self.get_queryset().filter(is_resolved=False)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
