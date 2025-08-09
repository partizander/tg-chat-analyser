from .messages_per_month import MessagesPerMonth
from .messages_per_hour import MessagesPerHour

REGISTRY = {
    "messages_per_month": MessagesPerMonth,
    "messages_per_hour": MessagesPerHour,
}