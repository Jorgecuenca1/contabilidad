/**
 * Sistema de validación de formularios para Sistema Contable Multiempresa
 * Validaciones específicas para Colombia y contabilidad
 */

class FormValidator {
    constructor() {
        this.initializeValidation();
        this.setupCustomValidators();
    }

    initializeValidation() {
        // Activar validación de Bootstrap
        document.addEventListener('DOMContentLoaded', () => {
            this.enableBootstrapValidation();
            this.setupFormEventListeners();
            this.setupCustomFieldValidators();
        });
    }

    enableBootstrapValidation() {
        // Aplicar validación de Bootstrap a todos los formularios
        const forms = document.querySelectorAll('.needs-validation');
        
        forms.forEach(form => {
            form.addEventListener('submit', (event) => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    this.showValidationErrors(form);
                }
                form.classList.add('was-validated');
            }, false);
        });
    }

    setupFormEventListeners() {
        // Validación en tiempo real
        document.addEventListener('blur', (event) => {
            if (event.target.matches('input, select, textarea')) {
                this.validateField(event.target);
            }
        }, true);

        document.addEventListener('input', (event) => {
            if (event.target.matches('input[type="text"], input[type="email"], textarea')) {
                this.clearFieldErrors(event.target);
            }
        }, true);
    }

    setupCustomFieldValidators() {
        // Validación de NIT
        document.addEventListener('blur', (event) => {
            if (event.target.name === 'document_number' && 
                this.getDocumentType(event.target) === 'NIT') {
                this.validateNIT(event.target);
            }
        });

        // Validación de email
        document.addEventListener('blur', (event) => {
            if (event.target.type === 'email') {
                this.validateEmail(event.target);
            }
        });

        // Validación de números de teléfono
        document.addEventListener('blur', (event) => {
            if (event.target.name === 'phone' || event.target.name === 'mobile') {
                this.validatePhone(event.target);
            }
        });

        // Validación de códigos CIIU
        document.addEventListener('blur', (event) => {
            if (event.target.name === 'ciiu_code') {
                this.validateCIIUCode(event.target);
            }
        });

        // Validación de montos
        document.addEventListener('blur', (event) => {
            if (event.target.type === 'number' && event.target.step === '0.01') {
                this.validateAmount(event.target);
            }
        });
    }

    validateField(field) {
        const isValid = field.checkValidity();
        
        if (!isValid) {
            this.showFieldError(field, field.validationMessage);
        } else {
            this.clearFieldErrors(field);
        }

        return isValid;
    }

    validateNIT(field) {
        const nit = field.value.trim();
        
        if (!nit) return true;

        // Remover guiones y espacios
        const nitClean = nit.replace(/[-\s]/g, '');

        // Validar formato
        if (!/^\d{8,15}$/.test(nitClean)) {
            this.showFieldError(field, 'El NIT debe tener entre 8 y 15 dígitos');
            return false;
        }

        // Calcular dígito de verificación
        const dv = this.calculateNITDigit(nitClean);
        
        // Si el NIT incluye DV, validar
        if (nit.includes('-')) {
            const parts = nit.split('-');
            if (parts.length === 2 && parts[1] !== dv) {
                this.showFieldError(field, `Dígito de verificación incorrecto. Debería ser: ${dv}`);
                return false;
            }
        } else {
            // Actualizar el campo DV si existe
            const dvField = document.querySelector('[name="verification_digit"]');
            if (dvField) {
                dvField.value = dv;
            }
        }

        this.clearFieldErrors(field);
        return true;
    }

    calculateNITDigit(nit) {
        const factors = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71];
        let sum = 0;

        for (let i = 0; i < nit.length && i < factors.length; i++) {
            sum += parseInt(nit.charAt(nit.length - 1 - i)) * factors[i];
        }

        const remainder = sum % 11;
        return remainder > 1 ? (11 - remainder).toString() : remainder.toString();
    }

    validateEmail(field) {
        const email = field.value.trim();
        
        if (!email) return true;

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!emailRegex.test(email)) {
            this.showFieldError(field, 'Ingrese un email válido');
            return false;
        }

        this.clearFieldErrors(field);
        return true;
    }

    validatePhone(field) {
        const phone = field.value.trim();
        
        if (!phone) return true;

        // Formato colombiano: 7-10 dígitos
        const phoneRegex = /^[0-9]{7,10}$/;
        
        if (!phoneRegex.test(phone.replace(/[-\s]/g, ''))) {
            this.showFieldError(field, 'Ingrese un número de teléfono válido (7-10 dígitos)');
            return false;
        }

        this.clearFieldErrors(field);
        return true;
    }

    validateCIIUCode(field) {
        const ciiu = field.value.trim();
        
        if (!ciiu) return true;

        if (!/^\d{4}$/.test(ciiu)) {
            this.showFieldError(field, 'El código CIIU debe tener exactamente 4 dígitos');
            return false;
        }

        this.clearFieldErrors(field);
        return true;
    }

    validateAmount(field) {
        const amount = parseFloat(field.value);
        
        if (isNaN(amount)) return true;

        if (amount < 0) {
            this.showFieldError(field, 'El valor no puede ser negativo');
            return false;
        }

        if (field.min && amount < parseFloat(field.min)) {
            this.showFieldError(field, `El valor mínimo es ${field.min}`);
            return false;
        }

        if (field.max && amount > parseFloat(field.max)) {
            this.showFieldError(field, `El valor máximo es ${field.max}`);
            return false;
        }

        this.clearFieldErrors(field);
        return true;
    }

    getDocumentType(field) {
        const form = field.closest('form');
        const documentTypeField = form.querySelector('[name="document_type"]');
        return documentTypeField ? documentTypeField.value : '';
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');

        // Remover mensaje de error existente
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }

        // Crear nuevo mensaje de error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldErrors(field) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');

        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    showValidationErrors(form) {
        const invalidFields = form.querySelectorAll('.is-invalid, :invalid');
        
        if (invalidFields.length > 0) {
            // Scroll al primer campo inválido
            invalidFields[0].scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
            
            // Mostrar notificación
            this.showNotification('Por favor corrija los errores en el formulario', 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Crear notificación usando Bootstrap Toast o Alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alertDiv);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    setupCustomValidators() {
        // Validador personalizado para fechas de vencimiento
        this.addDateRangeValidator();
        
        // Validador para partida doble en asientos contables
        this.addDoubleEntryValidator();
        
        // Validador para formularios de terceros
        this.addThirdPartyValidator();
    }

    addDateRangeValidator() {
        document.addEventListener('change', (event) => {
            const field = event.target;
            
            if (field.name === 'due_date' || field.name === 'end_date') {
                const form = field.closest('form');
                const startField = form.querySelector('[name="invoice_date"], [name="start_date"]');
                
                if (startField && startField.value && field.value) {
                    if (new Date(field.value) <= new Date(startField.value)) {
                        this.showFieldError(field, 'La fecha final debe ser posterior a la fecha inicial');
                    } else {
                        this.clearFieldErrors(field);
                    }
                }
            }
        });
    }

    addDoubleEntryValidator() {
        // Validar que débitos = créditos en asientos contables
        document.addEventListener('input', (event) => {
            if (event.target.name && event.target.name.includes('amount')) {
                this.validateDoubleEntry(event.target);
            }
        });
    }

    validateDoubleEntry(field) {
        const form = field.closest('form');
        const debitFields = form.querySelectorAll('[name*="debit"]');
        const creditFields = form.querySelectorAll('[name*="credit"]');

        let totalDebits = 0;
        let totalCredits = 0;

        debitFields.forEach(field => {
            const value = parseFloat(field.value) || 0;
            totalDebits += value;
        });

        creditFields.forEach(field => {
            const value = parseFloat(field.value) || 0;
            totalCredits += value;
        });

        const balanceDiv = form.querySelector('.balance-indicator');
        if (balanceDiv) {
            const difference = totalDebits - totalCredits;
            
            if (Math.abs(difference) < 0.01) {
                balanceDiv.innerHTML = '<span class="badge bg-success">Balanceado</span>';
            } else {
                balanceDiv.innerHTML = `<span class="badge bg-warning">Diferencia: $${Math.abs(difference).toFixed(2)}</span>`;
            }
        }
    }

    addThirdPartyValidator() {
        // Validar que al menos un tipo esté seleccionado
        document.addEventListener('change', (event) => {
            if (event.target.type === 'checkbox' && event.target.name.startsWith('is_')) {
                this.validateThirdPartyTypes(event.target);
            }
        });
    }

    validateThirdPartyTypes(checkbox) {
        const form = checkbox.closest('form');
        const typeCheckboxes = form.querySelectorAll('[name^="is_"]:not([name="is_active"])');
        
        const anyChecked = Array.from(typeCheckboxes).some(cb => cb.checked);
        
        const errorContainer = form.querySelector('.third-party-types-error');
        
        if (!anyChecked) {
            if (!errorContainer) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger third-party-types-error mt-2';
                errorDiv.textContent = 'Debe seleccionar al menos un tipo (Cliente, Proveedor, etc.)';
                
                const typesSection = form.querySelector('.types-section') || 
                                   typeCheckboxes[0].closest('.row') || 
                                   typeCheckboxes[0].parentNode;
                typesSection.appendChild(errorDiv);
            }
        } else {
            if (errorContainer) {
                errorContainer.remove();
            }
        }
    }

    // Método público para validar formulario completo
    validateForm(form) {
        const isValid = form.checkValidity();
        form.classList.add('was-validated');
        
        if (!isValid) {
            this.showValidationErrors(form);
        }
        
        return isValid;
    }
}

// Funciones globales de utilidad para las plantillas
window.FormValidator = FormValidator;

// Inicializar validador
const formValidator = new FormValidator();

// Funciones específicas para casos de uso
window.togglePersonFields = function(personType) {
    const naturalFields = document.querySelectorAll('.natural-field');
    const juridicaFields = document.querySelectorAll('.juridica-field');
    
    if (personType === 'NATURAL') {
        naturalFields.forEach(field => {
            field.parentNode.style.display = '';
            field.required = true;
        });
        juridicaFields.forEach(field => {
            field.parentNode.style.display = 'none';
            field.required = false;
        });
    } else if (personType === 'JURIDICA') {
        naturalFields.forEach(field => {
            field.parentNode.style.display = 'none';
            field.required = false;
        });
        juridicaFields.forEach(field => {
            field.parentNode.style.display = '';
            field.required = true;
        });
    }
};

window.handleDocumentType = function(documentType) {
    const dvField = document.querySelector('[name="verification_digit"]');
    
    if (dvField) {
        if (documentType === 'NIT') {
            dvField.parentNode.style.display = '';
            dvField.readOnly = true;
        } else {
            dvField.parentNode.style.display = 'none';
            dvField.value = '';
        }
    }
};

window.calculateDV = function() {
    const nitField = document.querySelector('[name="document_number"]');
    const dvField = document.querySelector('[name="verification_digit"]');
    const documentType = document.querySelector('[name="document_type"]').value;
    
    if (documentType === 'NIT' && nitField.value && dvField) {
        const dv = formValidator.calculateNITDigit(nitField.value);
        dvField.value = dv;
    }
};

// Formateo de números
window.formatCurrency = function(input) {
    const value = parseFloat(input.value);
    if (!isNaN(value)) {
        input.value = value.toFixed(2);
    }
};

// Auto-completar campos
window.setupAutoComplete = function(selector, dataSource) {
    // Implementar autocompletado si es necesario
    console.log('Auto-complete setup for:', selector);
};