from django.db import models

class ChatSession(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)
    summary=models.TextField(blank=True,null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Session{self.id}"

class Message(models.Model):
    session=models.ForeignKey(ChatSession,on_delete=models.CASCADE,related_name="messages")
    role=models.CharField(max_length=10)
    content=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.role}:{self.content[:30]}"