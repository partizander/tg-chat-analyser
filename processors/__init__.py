from .registry import REGISTRY
# импортируем процессоры, чтобы они зарегистрировались
from . import messages_per_hour  # noqa: F401
from . import messages_per_month  # noqa: F401
from . import top_senders  # noqa: F401
from . import top_authors_by_text_length  # noqa: F401
from . import message_type_share
from . import media_type_evolution
from . import top_reactions