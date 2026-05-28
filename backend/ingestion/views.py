from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import csv
import json
import logging
from ingestion.models import IngestionJob, RawRecord
from ingestion.serializers import IngestionJobSerializer, RawRecordSerializer
from ingestion.services import IngestionService
from breathe.permissions import IsAuthenticatedAndSetOrganization

logger = logging.getLogger(__name__)


class IngestionJobViewSet(viewsets.ModelViewSet):
    """
    Ingestion jobs - file uploads and processing.
    """
    serializer_class = IngestionJobSerializer
    permission_classes = [IsAuthenticatedAndSetOrganization]
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        if hasattr(self.request, 'organization') and self.request.organization:
            return IngestionJob.objects.filter(organization=self.request.organization)
        return IngestionJob.objects.none()
    
    @action(detail=False, methods=['post'], parser_classes=(MultiPartParser, FormParser))
    def upload(self, request):
        """Upload a file for ingestion."""
        logger.info(f"Upload request from {request.user}")
        file_obj = request.FILES.get('file')
        data_source_id = request.data.get('data_source_id')
        
        logger.info(f"  file_obj: {file_obj.name if file_obj else None}")
        logger.info(f"  data_source_id: {data_source_id}")
        logger.info(f"  request.organization: {request.organization if hasattr(request, 'organization') else 'NOT SET'}")
        
        if not file_obj or not data_source_id:
            return Response(
                {'error': 'file and data_source_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create ingestion job
            from data_sources.models import DataSource
            logger.info(f"Looking up DataSource {data_source_id} in org {request.organization}")
            data_source = DataSource.objects.get(
                id=data_source_id,
                organization=request.organization
            )
            logger.info(f"Found DataSource: {data_source.name}")
            
            # Save file
            file_path = f"uploads/{request.organization.id}/{file_obj.name}"
            file_content = file_obj.read()
            default_storage.save(file_path, ContentFile(file_content))
            logger.info(f"File saved to {file_path}")
            
            # Create job
            job = IngestionJob.objects.create(
                organization=request.organization,
                data_source=data_source,
                file_name=file_obj.name,
                file_path=file_path,
                file_size=file_obj.size,
                uploaded_by=request.user,
                status='pending'
            )
            logger.info(f"Created IngestionJob {job.id}")
            
            # Process job
            service = IngestionService()
            service.process_job(job)
            logger.info(f"Processed job {job.id}")
            
            serializer = self.get_serializer(job)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Upload error: {type(e).__name__}: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def raw_records(self, request, pk=None):
        """Get raw records from a job."""
        job = self.get_object()
        raw_records = job.raw_records.all()
        serializer = RawRecordSerializer(raw_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def error_summary(self, request, pk=None):
        """Get error summary for a failed job."""
        job = self.get_object()
        if job.status != 'failed':
            return Response(
                {'error': 'Job did not fail'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'status': job.status,
            'error': job.processing_error,
            'total_records': job.total_records,
            'invalid_records': job.invalid_records,
        })
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocess a failed job."""
        job = self.get_object()
        
        if job.status != 'failed':
            return Response(
                {'error': 'Only failed jobs can be reprocessed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            job.status = 'pending'
            job.processing_error = ''
            job.save()
            
            service = IngestionService()
            service.process_job(job)
            
            serializer = self.get_serializer(job)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
