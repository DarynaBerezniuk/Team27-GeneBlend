from django.db import models

class FunFacts(models.Model):
    fun_fact = models.TextField()

class ChromosomeInfo(models.Model):
    chromosome_info = models.TextField()

class EducationCard(models.Model):
    row = models.IntegerField()
    col = models.IntegerField()
    title = models.CharField(max_length=255)
    text = models.TextField()
    
    sections = models.JSONField() 
    tags = models.JSONField(default=list)
    
    image_svg = models.TextField(blank=True, null=True)
