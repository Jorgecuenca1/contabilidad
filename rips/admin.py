"""
Admin del módulo RIPS
Registros administrativos para gestión de RIPS
"""

from django.contrib import admin
from .models import (
    AttentionEpisode, EpisodeService, RIPSFile, RIPSTransaction,
    RIPSConsulta, RIPSProcedimiento, RIPSMedicamento,
    RIPSOtrosServicios, RIPSUsuario
)


@admin.register(AttentionEpisode)
class AttentionEpisodeAdmin(admin.ModelAdmin):
    list_display = ['episode_number', 'patient', 'episode_type', 'status', 'admission_date', 'discharge_date']
    list_filter = ['status', 'episode_type', 'is_billed']
    search_fields = ['episode_number', 'patient__third_party__first_name', 'patient__third_party__last_name']
    date_hierarchy = 'admission_date'
    raw_id_fields = ['patient', 'payer', 'admission', 'invoice']


@admin.register(EpisodeService)
class EpisodeServiceAdmin(admin.ModelAdmin):
    list_display = ['episode', 'service_type', 'service_cost', 'added_at']
    list_filter = ['service_type']
    search_fields = ['episode__episode_number']
    raw_id_fields = ['episode']


@admin.register(RIPSFile)
class RIPSFileAdmin(admin.ModelAdmin):
    list_display = ['file_number', 'status', 'period_start', 'period_end', 'total_invoices', 'total_amount']
    list_filter = ['status', 'file_format']
    search_fields = ['file_number', 'provider_nit']
    date_hierarchy = 'created_at'


@admin.register(RIPSTransaction)
class RIPSTransactionAdmin(admin.ModelAdmin):
    list_display = ['rips_file', 'invoice', 'note_type', 'created_at']
    list_filter = ['note_type']
    raw_id_fields = ['rips_file', 'invoice']


@admin.register(RIPSConsulta)
class RIPSConsultaAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'cod_consulta', 'fecha_inicio_atencion', 'cod_diagnostico_principal', 'vr_servicio']
    list_filter = ['fecha_inicio_atencion']
    search_fields = ['cod_consulta', 'cod_diagnostico_principal']
    raw_id_fields = ['transaction']


@admin.register(RIPSProcedimiento)
class RIPSProcedimientoAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'cod_procedimiento', 'fecha_inicio_atencion', 'cod_diagnostico_principal', 'vr_servicio']
    list_filter = ['fecha_inicio_atencion']
    search_fields = ['cod_procedimiento', 'cod_diagnostico_principal']
    raw_id_fields = ['transaction']


@admin.register(RIPSMedicamento)
class RIPSMedicamentoAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'nom_tecnologia_salud', 'cantidad_medicamento', 'vr_servicio']
    search_fields = ['cod_tecnologia_salud', 'nom_tecnologia_salud']
    raw_id_fields = ['transaction']


@admin.register(RIPSOtrosServicios)
class RIPSOtrosServiciosAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'nom_tecnologia_salud', 'tipo_os', 'cantidad_os', 'vr_servicio']
    list_filter = ['tipo_os']
    search_fields = ['nom_tecnologia_salud']
    raw_id_fields = ['transaction']


@admin.register(RIPSUsuario)
class RIPSUsuarioAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'num_documento_identificacion', 'tipo_usuario', 'fecha_nacimiento']
    list_filter = ['tipo_usuario', 'cod_sexo']
    search_fields = ['num_documento_identificacion']
    raw_id_fields = ['transaction']
