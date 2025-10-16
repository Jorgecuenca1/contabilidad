from django.contrib import admin
from .models import (
    Electrocardiogram, Echocardiogram, StressTest,
    HolterMonitoring, CardiovascularRiskAssessment,
    CardiologyConsultation
)

admin.site.register(Electrocardiogram)
admin.site.register(Echocardiogram)
admin.site.register(StressTest)
admin.site.register(HolterMonitoring)
admin.site.register(CardiovascularRiskAssessment)
admin.site.register(CardiologyConsultation)
