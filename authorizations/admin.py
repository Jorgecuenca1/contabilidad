"""
Admin del módulo Autorizaciones EPS
Administración completa de autorizaciones, contrarreferencias y documentos
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AuthorizationRequest, CounterReferral,
    AuthorizationAttachment, AuthorizationUsage
)


class AuthorizationAttachmentInline(admin.TabularInline):
    """Inline para documentos adjuntos a autorizaciones"""
    model = AuthorizationAttachment
    extra = 0
    fields = ('title', 'document_type', 'file', 'file_size', 'created_at')
    readonly_fields = ('file_size', 'created_at')
    fk_name = 'authorization_request'

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False


class AuthorizationUsageInline(admin.TabularInline):
    """Inline para uso de autorizaciones"""
    model = AuthorizationUsage
    extra = 0
    fields = ('usage_date', 'quantity_used', 'notes', 'created_by', 'created_at')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request, obj=None):
        return True


class CounterReferralAttachmentInline(admin.TabularInline):
    """Inline para documentos adjuntos a contrarreferencias"""
    model = AuthorizationAttachment
    extra = 0
    fields = ('title', 'document_type', 'file', 'file_size', 'created_at')
    readonly_fields = ('file_size', 'created_at')
    fk_name = 'counter_referral'

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuthorizationRequest)
class AuthorizationRequestAdmin(admin.ModelAdmin):
    """Admin para Solicitudes de Autorización"""

    list_display = [
        'authorization_number', 'patient', 'eps', 'service_type',
        'status_badge', 'priority_badge', 'request_date', 'expiration_date', 'is_expired_badge'
    ]

    list_filter = [
        'status', 'priority', 'service_type', 'eps', 'company',
        'request_date', 'submission_date', 'response_date'
    ]

    search_fields = [
        'authorization_number', 'patient__first_name', 'patient__last_name',
        'eps_authorization_number', 'diagnosis_code', 'diagnosis_description',
        'service_description', 'cups_code'
    ]

    date_hierarchy = 'request_date'

    readonly_fields = [
        'id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'response_date'
    ]

    raw_id_fields = ['patient', 'eps', 'requesting_physician', 'created_by', 'updated_by']

    inlines = [AuthorizationAttachmentInline, AuthorizationUsageInline]

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'authorization_number', 'status', 'priority'
            )
        }),
        ('Paciente y EPS', {
            'fields': (
                'patient', 'eps', 'requesting_physician'
            )
        }),
        ('Detalles del Servicio', {
            'fields': (
                'service_type', 'cups_code', 'service_description', 'quantity'
            )
        }),
        ('Diagnóstico', {
            'fields': (
                'diagnosis_code', 'diagnosis_description'
            )
        }),
        ('Justificación Médica', {
            'fields': (
                'medical_justification', 'clinical_history_summary'
            )
        }),
        ('Fechas', {
            'fields': (
                'request_date', 'submission_date', 'response_date', 'expiration_date'
            )
        }),
        ('Respuesta de la EPS', {
            'fields': (
                'eps_response', 'eps_authorization_number',
                'approved_quantity', 'denial_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'created_at', 'created_by', 'updated_at', 'updated_by'
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_selected', 'deny_selected', 'mark_as_under_review']

    def status_badge(self, obj):
        """Muestra el estado con color"""
        colors = {
            'draft': 'gray',
            'submitted': 'blue',
            'under_review': 'orange',
            'approved': 'green',
            'partial_approved': 'lightgreen',
            'denied': 'red',
            'cancelled': 'darkgray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def priority_badge(self, obj):
        """Muestra la prioridad con color"""
        colors = {
            'low': 'lightblue',
            'normal': 'gray',
            'high': 'orange',
            'urgent': 'red',
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'

    def is_expired_badge(self, obj):
        """Indica si la autorización está vencida"""
        if obj.is_expired():
            return format_html(
                '<span style="color: red; font-weight: bold;">VENCIDA</span>'
            )
        elif obj.expiration_date and obj.status == 'approved':
            return format_html(
                '<span style="color: green;">Vigente</span>'
            )
        return '-'
    is_expired_badge.short_description = 'Vigencia'

    def approve_selected(self, request, queryset):
        """Acción para aprobar autorizaciones seleccionadas"""
        # Solo cambiar estado, el resto debe hacerse manualmente
        count = queryset.filter(
            status__in=['submitted', 'under_review']
        ).update(status='under_review')

        self.message_user(
            request,
            f'{count} autorizaciones marcadas como en revisión. Complete los datos de aprobación manualmente.'
        )
    approve_selected.short_description = 'Marcar como en revisión para aprobar'

    def deny_selected(self, request, queryset):
        """Acción para negar autorizaciones"""
        count = queryset.filter(
            status__in=['submitted', 'under_review']
        ).update(status='denied')

        self.message_user(
            request,
            f'{count} autorizaciones marcadas como negadas. Agregue el motivo de negación manualmente.'
        )
    deny_selected.short_description = 'Marcar como negadas'

    def mark_as_under_review(self, request, queryset):
        """Marcar como en revisión"""
        count = queryset.filter(status='submitted').update(status='under_review')
        self.message_user(request, f'{count} autorizaciones marcadas como en revisión.')
    mark_as_under_review.short_description = 'Marcar como en revisión'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'patient', 'eps', 'requesting_physician',
            'company', 'created_by', 'updated_by'
        )


@admin.register(CounterReferral)
class CounterReferralAdmin(admin.ModelAdmin):
    """Admin para Contrarreferencias"""

    list_display = [
        'counter_referral_number', 'patient', 'authorization_request',
        'status_badge', 'service_date', 'sent_date'
    ]

    list_filter = [
        'status', 'eps', 'company', 'service_date',
        'creation_date', 'sent_date', 'requires_followup'
    ]

    search_fields = [
        'counter_referral_number', 'patient__first_name', 'patient__last_name',
        'authorization_request__authorization_number', 'final_diagnosis',
        'services_provided'
    ]

    date_hierarchy = 'creation_date'

    readonly_fields = ['id', 'created_at', 'created_by', 'updated_at']

    raw_id_fields = ['authorization_request', 'patient', 'eps', 'referring_physician', 'created_by']

    inlines = [CounterReferralAttachmentInline]

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'company', 'counter_referral_number', 'status'
            )
        }),
        ('Relación con Autorización', {
            'fields': (
                'authorization_request', 'patient', 'eps'
            )
        }),
        ('Médico y Servicio', {
            'fields': (
                'referring_physician', 'service_date', 'services_provided'
            )
        }),
        ('Resultados y Evolución', {
            'fields': (
                'treatment_results', 'patient_evolution', 'final_diagnosis'
            )
        }),
        ('Recomendaciones', {
            'fields': (
                'recommendations', 'requires_followup', 'followup_instructions'
            )
        }),
        ('Fechas', {
            'fields': (
                'creation_date', 'sent_date', 'received_date'
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_at', 'created_by', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_sent']

    def status_badge(self, obj):
        """Muestra el estado con color"""
        colors = {
            'pending': 'orange',
            'sent': 'blue',
            'received': 'green',
            'closed': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def mark_as_sent(self, request, queryset):
        """Marcar contrarreferencias como enviadas"""
        count = 0
        for cr in queryset.filter(status='pending'):
            cr.mark_as_sent()
            count += 1

        self.message_user(request, f'{count} contrarreferencias marcadas como enviadas.')
    mark_as_sent.short_description = 'Marcar como enviadas'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'patient', 'eps', 'authorization_request',
            'referring_physician', 'company', 'created_by'
        )


@admin.register(AuthorizationAttachment)
class AuthorizationAttachmentAdmin(admin.ModelAdmin):
    """Admin para Documentos Adjuntos"""

    list_display = [
        'title', 'document_type', 'authorization_or_counter_referral',
        'file_size_formatted', 'created_at', 'created_by'
    ]

    list_filter = [
        'document_type', 'created_at'
    ]

    search_fields = [
        'title', 'description',
        'authorization_request__authorization_number',
        'counter_referral__counter_referral_number'
    ]

    date_hierarchy = 'created_at'

    readonly_fields = ['id', 'file_size', 'created_at']

    raw_id_fields = ['authorization_request', 'counter_referral', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'title', 'description', 'document_type'
            )
        }),
        ('Relaciones', {
            'fields': (
                'authorization_request', 'counter_referral'
            )
        }),
        ('Archivo', {
            'fields': (
                'file', 'file_size'
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_at', 'created_by'
            )
        }),
    )

    def authorization_or_counter_referral(self, obj):
        """Muestra a qué está adjunto el documento"""
        if obj.authorization_request:
            return format_html(
                'Autorización: <strong>{}</strong>',
                obj.authorization_request.authorization_number
            )
        elif obj.counter_referral:
            return format_html(
                'Contrarreferencia: <strong>{}</strong>',
                obj.counter_referral.counter_referral_number
            )
        return '-'
    authorization_or_counter_referral.short_description = 'Adjunto a'

    def file_size_formatted(self, obj):
        """Muestra el tamaño del archivo formateado"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f'{obj.file_size} bytes'
            elif obj.file_size < 1024 * 1024:
                return f'{obj.file_size / 1024:.1f} KB'
            else:
                return f'{obj.file_size / (1024 * 1024):.1f} MB'
        return '-'
    file_size_formatted.short_description = 'Tamaño'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'authorization_request', 'counter_referral', 'created_by'
        )


@admin.register(AuthorizationUsage)
class AuthorizationUsageAdmin(admin.ModelAdmin):
    """Admin para Uso de Autorizaciones"""

    list_display = [
        'authorization_request', 'usage_date', 'quantity_used',
        'created_by', 'created_at'
    ]

    list_filter = [
        'usage_date', 'created_at'
    ]

    search_fields = [
        'authorization_request__authorization_number',
        'authorization_request__patient__first_name',
        'authorization_request__patient__last_name',
        'notes'
    ]

    date_hierarchy = 'usage_date'

    readonly_fields = ['id', 'created_at']

    raw_id_fields = ['authorization_request', 'medical_record', 'consultation', 'created_by']

    fieldsets = (
        ('Información General', {
            'fields': (
                'id', 'authorization_request', 'usage_date', 'quantity_used'
            )
        }),
        ('Relaciones con Atención', {
            'fields': (
                'medical_record', 'consultation'
            ),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': (
                'notes',
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_at', 'created_by'
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'authorization_request', 'authorization_request__patient',
            'created_by', 'medical_record', 'consultation'
        )
