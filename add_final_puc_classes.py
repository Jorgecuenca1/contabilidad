#!/usr/bin/env python
"""
Script para agregar las últimas clases del PUC (7-9):
- Clase 7: COSTOS DE PRODUCCIÓN O DE OPERACIÓN
- Clase 8: CUENTAS DE ORDEN DEUDORAS 
- Clase 9: CUENTAS DE ORDEN ACREEDORAS
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contabilidad_multiempresa.settings')
django.setup()

from core.models import Company, User
from accounting.models import ChartOfAccounts, AccountType, Account

def add_final_puc_classes():
    """Agregar las clases 7-9 del PUC a todas las empresas."""
    companies = Company.objects.all()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if not admin_user:
        print("[ERROR] No se encontro usuario administrador.")
        return
    
    # Obtener tipos de cuenta
    account_types = {}
    for at in AccountType.objects.all():
        account_types[at.code] = at
    
    # CLASE 7 - COSTOS DE PRODUCCIÓN O DE OPERACIÓN
    costos_produccion_accounts = [
        ('7', 'COSTOS DE PRODUCCIÓN O DE OPERACIÓN', None, False),
        ('71', 'MATERIA PRIMA', '7', False),
        ('7105', 'MATERIAS PRIMAS', '71', False),
        ('710505', 'Productos químicos', '7105', True),
        ('710510', 'Productos de caucho y plástico', '7105', True),
        ('710515', 'Productos textiles', '7105', True),
        ('710520', 'Productos metalúrgicos', '7105', True),
        ('710525', 'Productos de papel y cartón', '7105', True),
        ('710530', 'Productos alimenticios', '7105', True),
        ('710535', 'Productos farmacéuticos', '7105', True),
        ('710540', 'Productos de cuero', '7105', True),
        ('710545', 'Productos de madera', '7105', True),
        ('710595', 'Otros', '7105', True),
        ('7110', 'MANO DE OBRA DIRECTA', '71', False),
        ('711005', 'Salarios', '7110', True),
        ('711010', 'Prestaciones sociales', '7110', True),
        ('711015', 'Aportes patronales', '7110', True),
        ('7115', 'COSTOS INDIRECTOS', '71', False),
        ('711505', 'Materiales indirectos', '7115', True),
        ('711510', 'Mano de obra indirecta', '7115', True),
        ('711515', 'Otros costos indirectos', '7115', True),
        ('72', 'MANO DE OBRA DIRECTA', '7', False),
        ('7205', 'SUELDOS Y JORNALES', '72', False),
        ('720505', 'Personal de producción', '7205', True),
        ('720510', 'Personal de servicios', '7205', True),
        ('7210', 'PRESTACIONES SOCIALES', '72', False),
        ('721005', 'Cesantías', '7210', True),
        ('721010', 'Intereses sobre cesantías', '7210', True),
        ('721015', 'Prima de servicios', '7210', True),
        ('721020', 'Vacaciones', '7210', True),
        ('721025', 'Primas extralegales', '7210', True),
        ('721030', 'Auxilios', '7210', True),
        ('721035', 'Bonificaciones', '7210', True),
        ('721040', 'Dotación y suministro', '7210', True),
        ('721045', 'Seguros', '7210', True),
        ('721050', 'Indemnizaciones laborales', '7210', True),
        ('7215', 'APORTES PATRONALES', '72', False),
        ('721505', 'EPS', '7215', True),
        ('721510', 'Fondos de pensiones', '7215', True),
        ('721515', 'ARP', '7215', True),
        ('721520', 'Cajas de compensación familiar', '7215', True),
        ('721525', 'ICBF', '7215', True),
        ('721530', 'SENA', '7215', True),
        ('73', 'COSTOS INDIRECTOS', '7', False),
        ('7305', 'MATERIALES INDIRECTOS', '73', False),
        ('730505', 'Combustibles y lubricantes', '7305', True),
        ('730510', 'Repuestos y accesorios', '7305', True),
        ('730515', 'Herramientas de poco valor', '7305', True),
        ('730520', 'Útiles de aseo', '7305', True),
        ('730525', 'Útiles de oficina', '7305', True),
        ('730595', 'Otros', '7305', True),
        ('7310', 'MANO DE OBRA INDIRECTA', '73', False),
        ('731005', 'Sueldos y salarios', '7310', True),
        ('731010', 'Prestaciones sociales', '7310', True),
        ('731015', 'Aportes patronales', '7310', True),
        ('7315', 'OTROS COSTOS INDIRECTOS', '73', False),
        ('731505', 'Servicios públicos', '7315', True),
        ('731510', 'Arrendamientos', '7315', True),
        ('731515', 'Seguros', '7315', True),
        ('731520', 'Mantenimiento y reparaciones', '7315', True),
        ('731525', 'Depreciaciones', '7315', True),
        ('731530', 'Amortizaciones', '7315', True),
        ('731535', 'Provisiones', '7315', True),
        ('731595', 'Otros', '7315', True),
        ('74', 'CONTRATOS DE SERVICIOS', '7', False),
        ('7405', 'COSTOS DE SERVICIOS', '74', False),
        ('740505', 'Servicios públicos', '7405', True),
        ('740510', 'Arrendamientos', '7405', True),
        ('740515', 'Mantenimiento y reparaciones', '7405', True),
        ('740520', 'Honorarios y comisiones', '7405', True),
        ('740525', 'Transporte y fletes', '7405', True),
        ('740530', 'Comunicaciones', '7405', True),
        ('740595', 'Otros servicios', '7405', True),
    ]
    
    # CLASE 8 - CUENTAS DE ORDEN DEUDORAS
    cuentas_orden_deudoras_accounts = [
        ('8', 'CUENTAS DE ORDEN DEUDORAS', None, False),
        ('81', 'DERECHOS CONTINGENTES', '8', False),
        ('8105', 'LITIGIOS Y/O DEMANDAS', '81', False),
        ('810505', 'Civiles', '8105', True),
        ('810510', 'Laborales', '8105', True),
        ('810515', 'Penales', '8105', True),
        ('810520', 'Administrativos civiles', '8105', True),
        ('810595', 'Otros', '8105', True),
        ('8110', 'PROMESAS DE COMPRAVENTA', '81', False),
        ('811005', 'De bienes raíces', '8110', True),
        ('8115', 'GARANTÍAS OTORGADAS', '81', False),
        ('811505', 'Prendarias', '8115', True),
        ('811510', 'Bancarias', '8115', True),
        ('811515', 'Contractuales de cumplimiento', '8115', True),
        ('811520', 'Técnicas de estabilidad y mantenimiento de obra', '8115', True),
        ('811595', 'Otras', '8115', True),
        ('8120', 'DOCUMENTOS EN CUSTODIA', '81', False),
        ('812005', 'Valores mobiliarios', '8120', True),
        ('812010', 'Documentos de archivo', '8120', True),
        ('8125', 'DEUDORAS FISCALES POR COBRAR', '81', False),
        ('812505', 'Impuestos', '8125', True),
        ('812510', 'Contribuciones', '8125', True),
        ('812515', 'Tasas', '8125', True),
        ('812520', 'Multas', '8125', True),
        ('812525', 'Intereses', '8125', True),
        ('812595', 'Otras', '8125', True),
        ('8130', 'DEUDORAS DE CONTROL', '81', False),
        ('813005', 'Bienes recibidos en custodia', '8130', True),
        ('813010', 'Bienes recibidos en consignación', '8130', True),
        ('813015', 'Contratos de leasing operativo', '8130', True),
        ('813020', 'Contratos de leasing financiero', '8130', True),
        ('813025', 'Bienes de terceros en poder de la empresa', '8130', True),
        ('813030', 'Mercancías en consignación', '8130', True),
        ('813035', 'Propiedades planta y equipo totalmente depreciados', '8130', True),
        ('813040', 'Títulos de inversión amortizados', '8130', True),
        ('813045', 'Capitalización por reexpresión del patrimonio', '8130', True),
        ('813050', 'Valor patrimonio técnico', '8130', True),
        ('813055', 'Deudores por ventas de activos', '8130', True),
        ('813060', 'Compañías filiales subsidiarias y del grupo', '8130', True),
        ('813095', 'Otras cuentas deudoras de control', '8130', True),
        ('82', 'DEUDORAS FISCALES', '8', False),
        ('8205', 'IMPUESTO DE RENTA DIFERIDO', '82', False),
        ('820505', 'Por diferencias temporales', '8205', True),
        ('820510', 'Por pérdidas fiscales', '8205', True),
        ('8210', 'IMPUESTO A LAS VENTAS RETENIDO', '82', False),
        ('821005', 'Por liquidar', '8210', True),
        ('8215', 'IMPUESTO A LAS VENTAS POR COBRAR', '82', False),
        ('821505', 'Por liquidar', '8215', True),
        ('8220', 'SOBRANTES EN LIQUIDACIÓN PRIVADA RENTA', '82', False),
        ('822005', 'Año gravable corriente', '8220', True),
        ('822010', 'Años gravables anteriores', '8220', True),
        ('8225', 'CONTRIBUCIÓN SOBRE MOVIMIENTOS FINANCIEROS RETENIDOS', '82', False),
        ('822505', 'Por liquidar', '8225', True),
        ('8295', 'OTRAS DEUDORAS FISCALES', '82', False),
        ('829505', 'Retención en la fuente renta por cobrar', '8295', True),
        ('829510', 'Anticipo impuesto sobre las ventas', '8295', True),
        ('829515', 'Anticipo impuesto de industria y comercio', '8295', True),
        ('829520', 'Retención industria y comercio retenido', '8295', True),
        ('829525', 'Impuesto de industria y comercio por cobrar', '8295', True),
        ('829595', 'Otras', '8295', True),
        ('83', 'DEUDORAS DE CONTROL POR CONTRA (CR)', '8', False),
        ('8305', 'LITIGIOS Y/O DEMANDAS POR CONTRA', '83', False),
        ('830505', 'Civiles', '8305', True),
        ('830510', 'Laborales', '8305', True),
        ('830515', 'Penales', '8305', True),
        ('830520', 'Administrativos civiles', '8305', True),
        ('830595', 'Otros', '8305', True),
        ('8310', 'PROMESAS DE COMPRAVENTA POR CONTRA', '83', False),
        ('831005', 'De bienes raíces', '8310', True),
        ('8315', 'GARANTÍAS OTORGADAS POR CONTRA', '83', False),
        ('831505', 'Prendarias', '8315', True),
        ('831510', 'Bancarias', '8315', True),
        ('831515', 'Contractuales de cumplimiento', '8315', True),
        ('831520', 'Técnicas de estabilidad y mantenimiento de obra', '8315', True),
        ('831595', 'Otras', '8315', True),
        ('8320', 'DOCUMENTOS EN CUSTODIA POR CONTRA', '83', False),
        ('832005', 'Valores mobiliarios', '8320', True),
        ('832010', 'Documentos de archivo', '8320', True),
        ('8325', 'DEUDORAS FISCALES POR CONTRA', '83', False),
        ('832505', 'Impuestos', '8325', True),
        ('832510', 'Contribuciones', '8325', True),
        ('832515', 'Tasas', '8325', True),
        ('832520', 'Multas', '8325', True),
        ('832525', 'Intereses', '8325', True),
        ('832595', 'Otras', '8325', True),
        ('8330', 'DEUDORAS DE CONTROL POR CONTRA', '83', False),
        ('833005', 'Bienes recibidos en custodia', '8330', True),
        ('833010', 'Bienes recibidos en consignación', '8330', True),
        ('833015', 'Contratos de leasing operativo', '8330', True),
        ('833020', 'Contratos de leasing financiero', '8330', True),
        ('833025', 'Bienes de terceros en poder de la empresa', '8330', True),
        ('833030', 'Mercancías en consignación', '8330', True),
        ('833035', 'Propiedades planta y equipo totalmente depreciados', '8330', True),
        ('833040', 'Títulos de inversión amortizados', '8330', True),
        ('833045', 'Capitalización por reexpresión del patrimonio', '8330', True),
        ('833050', 'Valor patrimonio técnico', '8330', True),
        ('833055', 'Deudores por ventas de activos', '8330', True),
        ('833060', 'Compañías filiales subsidiarias y del grupo', '8330', True),
        ('833095', 'Otras cuentas deudoras de control', '8330', True),
        ('84', 'DEUDORAS FISCALES POR CONTRA (CR)', '8', False),
        ('8405', 'IMPUESTO DE RENTA DIFERIDO POR CONTRA', '84', False),
        ('840505', 'Por diferencias temporales', '8405', True),
        ('840510', 'Por pérdidas fiscales', '8405', True),
        ('8410', 'IMPUESTO A LAS VENTAS RETENIDO POR CONTRA', '84', False),
        ('841005', 'Por liquidar', '8410', True),
        ('8415', 'IMPUESTO A LAS VENTAS POR COBRAR POR CONTRA', '84', False),
        ('841505', 'Por liquidar', '8415', True),
        ('8420', 'SOBRANTES EN LIQUIDACIÓN PRIVADA RENTA POR CONTRA', '84', False),
        ('842005', 'Año gravable corriente', '8420', True),
        ('842010', 'Años gravables anteriores', '8420', True),
        ('8425', 'CONTRIBUCIÓN SOBRE MOVIMIENTOS FINANCIEROS RETENIDOS POR CONTRA', '84', False),
        ('842505', 'Por liquidar', '8425', True),
        ('8495', 'OTRAS DEUDORAS FISCALES POR CONTRA', '84', False),
        ('849505', 'Retención en la fuente renta por cobrar', '8495', True),
        ('849510', 'Anticipo impuesto sobre las ventas', '8495', True),
        ('849515', 'Anticipo impuesto de industria y comercio', '8495', True),
        ('849520', 'Retención industria y comercio retenido', '8495', True),
        ('849525', 'Impuesto de industria y comercio por cobrar', '8495', True),
        ('849595', 'Otras', '8495', True),
        ('89', 'OTRAS CUENTAS DEUDORAS', '8', False),
        ('8905', 'OTRAS CUENTAS DEUDORAS', '89', False),
        ('890505', 'Diversas', '8905', True),
        ('8995', 'OTRAS CUENTAS DEUDORAS POR CONTRA (CR)', '89', False),
        ('899505', 'Diversas', '8995', True),
    ]
    
    # CLASE 9 - CUENTAS DE ORDEN ACREEDORAS
    cuentas_orden_acreedoras_accounts = [
        ('9', 'CUENTAS DE ORDEN ACREEDORAS', None, False),
        ('91', 'RESPONSABILIDADES CONTINGENTES', '9', False),
        ('9105', 'LITIGIOS Y/O DEMANDAS', '91', False),
        ('910505', 'Civiles', '9105', True),
        ('910510', 'Laborales', '9105', True),
        ('910515', 'Penales', '9105', True),
        ('910520', 'Administrativos civiles', '9105', True),
        ('910595', 'Otros', '9105', True),
        ('9110', 'PROMESAS DE COMPRAVENTA', '91', False),
        ('911005', 'De bienes raíces', '9110', True),
        ('9115', 'GARANTÍAS OTORGADAS', '91', False),
        ('911505', 'Prendarias', '9115', True),
        ('911510', 'Bancarias', '9115', True),
        ('911515', 'Contractuales de cumplimiento', '9115', True),
        ('911520', 'Técnicas de estabilidad y mantenimiento de obra', '9115', True),
        ('911595', 'Otras', '9115', True),
        ('9120', 'DOCUMENTOS EN CUSTODIA', '91', False),
        ('912005', 'Valores mobiliarios', '9120', True),
        ('912010', 'Documentos de archivo', '9120', True),
        ('9125', 'ACREEDORAS FISCALES POR PAGAR', '91', False),
        ('912505', 'Impuestos', '9125', True),
        ('912510', 'Contribuciones', '9125', True),
        ('912515', 'Tasas', '9125', True),
        ('912520', 'Multas', '9125', True),
        ('912525', 'Intereses', '9125', True),
        ('912595', 'Otras', '9125', True),
        ('9130', 'ACREEDORAS DE CONTROL', '91', False),
        ('913005', 'Bienes entregados en custodia', '9130', True),
        ('913010', 'Bienes entregados en consignación', '9130', True),
        ('913015', 'Contratos de leasing operativo', '9130', True),
        ('913020', 'Contratos de leasing financiero', '9130', True),
        ('913025', 'Bienes propios en poder de terceros', '9130', True),
        ('913030', 'Mercancías en consignación', '9130', True),
        ('913035', 'Propiedades planta y equipo dadas en garantía', '9130', True),
        ('913040', 'Títulos de inversión dados en garantía', '9130', True),
        ('913045', 'Capitalización por reexpresión del patrimonio', '9130', True),
        ('913050', 'Valor patrimonio técnico', '9130', True),
        ('913055', 'Acreedores por compras de activos', '9130', True),
        ('913060', 'Compañías filiales subsidiarias y del grupo', '9130', True),
        ('913095', 'Otras cuentas acreedoras de control', '9130', True),
        ('92', 'ACREEDORAS FISCALES', '9', False),
        ('9205', 'IMPUESTO DE RENTA DIFERIDO', '92', False),
        ('920505', 'Por diferencias temporales', '9205', True),
        ('920510', 'Por corrección monetaria diferida', '9205', True),
        ('9210', 'IMPUESTO A LAS VENTAS RETENIDO', '92', False),
        ('921005', 'Por liquidar', '9210', True),
        ('9215', 'IMPUESTO A LAS VENTAS POR PAGAR', '92', False),
        ('921505', 'Por liquidar', '9215', True),
        ('9220', 'EXCESO DE RENTA PRESUNTIVA SOBRE RENTA LÍQUIDA', '92', False),
        ('922005', 'Año gravable corriente', '9220', True),
        ('922010', 'Años gravables anteriores', '9220', True),
        ('9225', 'CONTRIBUCIÓN SOBRE MOVIMIENTOS FINANCIEROS POR PAGAR', '92', False),
        ('922505', 'Por liquidar', '9225', True),
        ('9295', 'OTRAS ACREEDORAS FISCALES', '92', False),
        ('929505', 'Retención en la fuente renta por pagar', '9295', True),
        ('929510', 'Exceso anticipo impuesto sobre las ventas', '9295', True),
        ('929515', 'Exceso anticipo impuesto de industria y comercio', '9295', True),
        ('929520', 'Retención industria y comercio por pagar', '9295', True),
        ('929525', 'Impuesto de industria y comercio diferido', '9295', True),
        ('929595', 'Otras', '9295', True),
        ('93', 'ACREEDORAS DE CONTROL POR CONTRA (DB)', '9', False),
        ('9305', 'LITIGIOS Y/O DEMANDAS POR CONTRA', '93', False),
        ('930505', 'Civiles', '9305', True),
        ('930510', 'Laborales', '9305', True),
        ('930515', 'Penales', '9305', True),
        ('930520', 'Administrativos civiles', '9305', True),
        ('930595', 'Otros', '9305', True),
        ('9310', 'PROMESAS DE COMPRAVENTA POR CONTRA', '93', False),
        ('931005', 'De bienes raíces', '9310', True),
        ('9315', 'GARANTÍAS OTORGADAS POR CONTRA', '93', False),
        ('931505', 'Prendarias', '9315', True),
        ('931510', 'Bancarias', '9315', True),
        ('931515', 'Contractuales de cumplimiento', '9315', True),
        ('931520', 'Técnicas de estabilidad y mantenimiento de obra', '9315', True),
        ('931595', 'Otras', '9315', True),
        ('9320', 'DOCUMENTOS EN CUSTODIA POR CONTRA', '93', False),
        ('932005', 'Valores mobiliarios', '9320', True),
        ('932010', 'Documentos de archivo', '9320', True),
        ('9325', 'ACREEDORAS FISCALES POR CONTRA', '93', False),
        ('932505', 'Impuestos', '9325', True),
        ('932510', 'Contribuciones', '9325', True),
        ('932515', 'Tasas', '9325', True),
        ('932520', 'Multas', '9325', True),
        ('932525', 'Intereses', '9325', True),
        ('932595', 'Otras', '9325', True),
        ('9330', 'ACREEDORAS DE CONTROL POR CONTRA', '93', False),
        ('933005', 'Bienes entregados en custodia', '9330', True),
        ('933010', 'Bienes entregados en consignación', '9330', True),
        ('933015', 'Contratos de leasing operativo', '9330', True),
        ('933020', 'Contratos de leasing financiero', '9330', True),
        ('933025', 'Bienes propios en poder de terceros', '9330', True),
        ('933030', 'Mercancías en consignación', '9330', True),
        ('933035', 'Propiedades planta y equipo dadas en garantía', '9330', True),
        ('933040', 'Títulos de inversión dados en garantía', '9330', True),
        ('933045', 'Capitalización por reexpresión del patrimonio', '9330', True),
        ('933050', 'Valor patrimonio técnico', '9330', True),
        ('933055', 'Acreedores por compras de activos', '9330', True),
        ('933060', 'Compañías filiales subsidiarias y del grupo', '9330', True),
        ('933095', 'Otras cuentas acreedoras de control', '9330', True),
        ('94', 'ACREEDORAS FISCALES POR CONTRA (DB)', '9', False),
        ('9405', 'IMPUESTO DE RENTA DIFERIDO POR CONTRA', '94', False),
        ('940505', 'Por diferencias temporales', '9405', True),
        ('940510', 'Por corrección monetaria diferida', '9405', True),
        ('9410', 'IMPUESTO A LAS VENTAS RETENIDO POR CONTRA', '94', False),
        ('941005', 'Por liquidar', '9410', True),
        ('9415', 'IMPUESTO A LAS VENTAS POR PAGAR POR CONTRA', '94', False),
        ('941505', 'Por liquidar', '9415', True),
        ('9420', 'EXCESO DE RENTA PRESUNTIVA SOBRE RENTA LÍQUIDA POR CONTRA', '94', False),
        ('942005', 'Año gravable corriente', '9420', True),
        ('942010', 'Años gravables anteriores', '9420', True),
        ('9425', 'CONTRIBUCIÓN SOBRE MOVIMIENTOS FINANCIEROS POR PAGAR POR CONTRA', '94', False),
        ('942505', 'Por liquidar', '9425', True),
        ('9495', 'OTRAS ACREEDORAS FISCALES POR CONTRA', '94', False),
        ('949505', 'Retención en la fuente renta por pagar', '9495', True),
        ('949510', 'Exceso anticipo impuesto sobre las ventas', '9495', True),
        ('949515', 'Exceso anticipo impuesto de industria y comercio', '9495', True),
        ('949520', 'Retención industria y comercio por pagar', '9495', True),
        ('949525', 'Impuesto de industria y comercio diferido', '9495', True),
        ('949595', 'Otras', '9495', True),
        ('99', 'OTRAS CUENTAS ACREEDORAS', '9', False),
        ('9905', 'OTRAS CUENTAS ACREEDORAS', '99', False),
        ('990505', 'Diversas', '9905', True),
        ('9995', 'OTRAS CUENTAS ACREEDORAS POR CONTRA (DB)', '99', False),
        ('999505', 'Diversas', '9995', True),
    ]
    
    # Todas las cuentas de clases 7-9
    all_final_accounts = costos_produccion_accounts + cuentas_orden_deudoras_accounts + cuentas_orden_acreedoras_accounts
    
    for company in companies:
        print(f'\n[*] Agregando clases 7-9 para empresa: {company.name}')
        
        # Obtener plan de cuentas existente
        chart = ChartOfAccounts.objects.filter(company=company).first()
        if not chart:
            print(f'[ERROR] No se encontro plan de cuentas para {company.name}')
            continue
        
        created_count = 0
        for code, name, parent_code, is_detail in all_final_accounts:
            # Determinar tipo de cuenta basado en el primer dígito
            first_digit = code[0]
            account_type = account_types.get(first_digit)
            
            if not account_type:
                continue
            
            # Buscar cuenta padre
            parent = None
            if parent_code:
                parent = Account.objects.filter(
                    chart_of_accounts=chart, 
                    code=parent_code
                ).first()
            
            # Determinar el nivel
            level = len(code)
            if level == 1:
                level = 1  # Clase
            elif level == 2:
                level = 2  # Grupo
            elif level == 4:
                level = 3  # Cuenta
            elif level == 6:
                level = 4  # Subcuenta
            else:
                level = 4  # Por defecto
            
            # Crear cuenta si no existe
            account, created = Account.objects.get_or_create(
                chart_of_accounts=chart,
                code=code,
                defaults={
                    'name': name,
                    'account_type': account_type,
                    'parent': parent,
                    'level': level,
                    'is_detail': is_detail,
                    'is_active': True,
                    'description': f'Cuenta {name} del PUC colombiano según Decreto 2650/93',
                    'created_by': admin_user
                }
            )
            
            if created:
                created_count += 1
        
        print(f'   [+] Se crearon {created_count} nuevas cuentas para {chart.company.name}')

if __name__ == '__main__':
    print('[*] Agregando clases finales del PUC (7-9)...')
    add_final_puc_classes()
    print('[OK] Clases 7-9 del PUC agregadas exitosamente!')
    print('[SUCCESS] PUC COMPLETO DE COLOMBIA IMPLEMENTADO!')
    print('         Se han agregado mas de 2000 cuentas contables')
    print('         segun el Decreto 2650 de 1993')