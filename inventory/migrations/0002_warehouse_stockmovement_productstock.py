# Generated manually for inventory stock management models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventory', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('address', models.TextField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_main_warehouse', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warehouses', to='core.company')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Bodega',
                'verbose_name_plural': 'Bodegas',
                'db_table': 'inventory_warehouses',
                'ordering': ['code'],
                'unique_together': {('company', 'code')},
            },
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('movement_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('movement_type', models.CharField(choices=[('entry', 'Entrada'), ('exit', 'Salida'), ('adjustment', 'Ajuste'), ('transfer', 'Transferencia'), ('initial', 'Inventario Inicial')], max_length=20)),
                ('movement_reason', models.CharField(choices=[('purchase', 'Compra'), ('sale', 'Venta'), ('return_customer', 'Devolución de Cliente'), ('return_supplier', 'Devolución a Proveedor'), ('damage', 'Daño/Pérdida'), ('obsolescence', 'Obsolescencia'), ('count_adjustment', 'Ajuste por Conteo'), ('cost_adjustment', 'Ajuste de Costo'), ('transfer_in', 'Transferencia Entrada'), ('transfer_out', 'Transferencia Salida'), ('production', 'Producción'), ('consumption', 'Consumo'), ('initial_inventory', 'Inventario Inicial'), ('other', 'Otro')], max_length=20)),
                ('quantity', models.DecimalField(decimal_places=4, max_digits=15)),
                ('unit_cost', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('total_cost', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('document_type', models.CharField(blank=True, max_length=50)),
                ('document_number', models.CharField(blank=True, max_length=50)),
                ('reference', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('lot_number', models.CharField(blank=True, max_length=50)),
                ('serial_number', models.CharField(blank=True, max_length=50)),
                ('expiration_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements', to='core.company')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('journal_entry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_movements', to='accounting.journalentry')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements', to='inventory.product')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements', to='inventory.warehouse')),
                ('warehouse_destination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements_destination', to='inventory.warehouse')),
            ],
            options={
                'verbose_name': 'Movimiento de Stock',
                'verbose_name_plural': 'Movimientos de Stock',
                'db_table': 'inventory_stock_movements',
                'ordering': ['-movement_date', '-created_at'],
                'indexes': [
                    models.Index(fields=['company', 'movement_date'], name='inventory_s_company_2fb06b_idx'),
                    models.Index(fields=['product', 'warehouse'], name='inventory_s_product_95e2a4_idx'),
                    models.Index(fields=['movement_type'], name='inventory_s_movemen_21f1a2_idx'),
                    models.Index(fields=['document_type', 'document_number'], name='inventory_s_documen_1e5b7c_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ProductStock',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quantity_on_hand', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('quantity_reserved', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('quantity_available', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('average_cost', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('last_cost', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('total_value', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('last_movement_date', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_stocks', to='core.company')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stocks', to='inventory.product')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_stocks', to='inventory.warehouse')),
            ],
            options={
                'verbose_name': 'Stock de Producto',
                'verbose_name_plural': 'Stock de Productos',
                'db_table': 'inventory_product_stocks',
                'ordering': ['product__code', 'warehouse__code'],
                'unique_together': {('company', 'product', 'warehouse')},
                'indexes': [
                    models.Index(fields=['product', 'warehouse'], name='inventory_p_product_8b9c5d_idx'),
                    models.Index(fields=['quantity_on_hand'], name='inventory_p_quantit_3a7f12_idx'),
                ],
            },
        ),
    ]