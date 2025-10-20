/**
 * Form Validation Module
 * Real-time form validation with visual feedback
 */

class FormValidator {
  constructor(formSelector, options = {}) {
    this.form = typeof formSelector === 'string'
      ? document.querySelector(formSelector)
      : formSelector;

    if (!this.form) {
      console.error('Form not found:', formSelector);
      return;
    }

    this.options = {
      validateOnBlur: true,
      validateOnInput: true,
      showSuccessState: true,
      scrollToError: true,
      ...options
    };

    this.fields = [];
    this.init();
  }

  /**
   * Initialize form validation
   */
  init() {
    // Get all validatable fields
    this.fields = Array.from(this.form.querySelectorAll('input, select, textarea'))
      .filter(field => field.type !== 'hidden' && field.type !== 'submit');

    // Add event listeners
    this.fields.forEach(field => {
      if (this.options.validateOnBlur) {
        field.addEventListener('blur', () => this.validateField(field));
      }

      if (this.options.validateOnInput) {
        field.addEventListener('input', () => {
          // Only validate on input if field was previously invalid
          if (field.classList.contains('is-invalid')) {
            this.validateField(field);
          }
        });
      }
    });

    // Prevent form submission if invalid
    this.form.addEventListener('submit', (e) => this.handleSubmit(e));
  }

  /**
   * Validate a single field
   * @param {HTMLElement} field - The field to validate
   * @returns {boolean} - True if valid
   */
  validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';

    // Check if field is required
    if (field.required && !value) {
      isValid = false;
      errorMessage = 'This field is required';
    }

    // Check custom validation
    else if (!field.checkValidity()) {
      isValid = false;
      errorMessage = field.validationMessage || 'Please enter a valid value';
    }

    // Check pattern if exists
    else if (field.pattern && value) {
      const regex = new RegExp(field.pattern);
      if (!regex.test(value)) {
        isValid = false;
        errorMessage = field.title || 'Please match the requested format';
      }
    }

    // Check min/max for numbers
    else if (field.type === 'number') {
      const num = parseFloat(value);
      if (field.min && num < parseFloat(field.min)) {
        isValid = false;
        errorMessage = `Minimum value is ${field.min}`;
      } else if (field.max && num > parseFloat(field.max)) {
        isValid = false;
        errorMessage = `Maximum value is ${field.max}`;
      }
    }

    // Update field UI
    this.updateFieldUI(field, isValid, errorMessage);

    return isValid;
  }

  /**
   * Update field UI based on validation state
   * @param {HTMLElement} field - The field element
   * @param {boolean} isValid - Whether field is valid
   * @param {string} errorMessage - Error message to display
   */
  updateFieldUI(field, isValid, errorMessage = '') {
    // Remove existing classes
    field.classList.remove('is-valid', 'is-invalid');

    // Remove existing feedback
    const existingFeedback = field.parentElement.querySelector('.invalid-feedback, .valid-feedback');
    if (existingFeedback) {
      existingFeedback.remove();
    }

    if (isValid && this.options.showSuccessState && field.value.trim()) {
      // Show success state
      field.classList.add('is-valid');

      if (this.options.showSuccessState) {
        const feedback = document.createElement('div');
        feedback.className = 'valid-feedback d-block';
        feedback.textContent = '✓ Looks good!';
        field.parentElement.appendChild(feedback);
      }
    } else if (!isValid) {
      // Show error state
      field.classList.add('is-invalid');

      const feedback = document.createElement('div');
      feedback.className = 'invalid-feedback d-block';
      feedback.textContent = errorMessage;
      field.parentElement.appendChild(feedback);
    }
  }

  /**
   * Validate entire form
   * @returns {boolean} - True if all fields are valid
   */
  validateForm() {
    let isFormValid = true;
    let firstInvalidField = null;

    this.fields.forEach(field => {
      const isValid = this.validateField(field);
      if (!isValid) {
        isFormValid = false;
        if (!firstInvalidField) {
          firstInvalidField = field;
        }
      }
    });

    // Scroll to first invalid field
    if (!isFormValid && firstInvalidField && this.options.scrollToError) {
      firstInvalidField.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
      firstInvalidField.focus();
    }

    return isFormValid;
  }

  /**
   * Handle form submission
   * @param {Event} e - Submit event
   */
  handleSubmit(e) {
    if (!this.validateForm()) {
      e.preventDefault();

      // Show error toast if available
      if (window.toast) {
        window.toast.error('Please fill in all required fields correctly');
      }

      return false;
    }

    // Show loading state if button available
    const submitButton = this.form.querySelector('button[type="submit"]');
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
    }

    return true;
  }

  /**
   * Reset form validation
   */
  reset() {
    this.fields.forEach(field => {
      field.classList.remove('is-valid', 'is-invalid');
      const feedback = field.parentElement.querySelector('.invalid-feedback, .valid-feedback');
      if (feedback) {
        feedback.remove();
      }
    });

    const submitButton = this.form.querySelector('button[type="submit"]');
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = submitButton.dataset.originalText || 'Submit';
    }
  }

  /**
   * Add custom validation rule
   * @param {string} fieldSelector - Selector for the field
   * @param {Function} validator - Validation function (returns {valid: boolean, message: string})
   */
  addCustomRule(fieldSelector, validator) {
    const field = this.form.querySelector(fieldSelector);
    if (!field) return;

    field.addEventListener('blur', () => {
      const result = validator(field.value, field);
      this.updateFieldUI(field, result.valid, result.message);
    });
  }
}

// Export for use in templates
window.FormValidator = FormValidator;
