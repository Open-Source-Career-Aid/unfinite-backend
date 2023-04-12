from django.db import models


# Create your models here.
class Topic(models.Model):
    title = models.CharField(max_length=255)
    synonyms = models.CharField(max_length=255)
    docids = models.CharField(max_length=255)
    in_edges = models.ManyToManyField('Edge', related_name='in_edges')
    out_edges = models.ManyToManyField('Edge', related_name='out_edges')

    def __str__(self):
        return f"{self.title}  | {self.docids}"

class Edge(models.Model):
    is_in_edge = models.BooleanField(default=False)
    is_out_edge = models.BooleanField(default=False)
    start_node = models.ForeignKey(Topic, related_name='start_node', on_delete=models.CASCADE)
    end_node = models.ForeignKey(Topic, related_name='end_node', on_delete=models.CASCADE)
    docid = models.CharField(max_length=255)
    weight = models.FloatField(default=0.0)

    def __str__(self):
        return f'{self.start_node.title} -> {self.end_node.title} | {self.docid}'
