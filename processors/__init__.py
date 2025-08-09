from .registry import REGISTRY
# импортируем процессоры, чтобы они зарегистрировались
from . import messages_per_hour  # noqa: F401
from . import messages_per_month  # noqa: F401
from . import top_senders  # noqa: F401
from . import top_authors_by_text_length  # noqa: F401
from . import message_type_share
from . import media_type_evolution
from . import top_reactions
from . import top_messages_by_reactions
from . import links_frequency_over_time
from . import geo_location_clusters
from . import top_bots_by_messages
from . import longest_messages_table
from . import top_stickers
from . import poll_lifetime_vs_votes
from . import new_members_activity
