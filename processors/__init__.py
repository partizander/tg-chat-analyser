from .registry import REGISTRY
# импортируем процессоры, чтобы они зарегистрировались
from . import active_users_per_month
from . import average_message_length_per_month
from . import first_time_posters_over_time
from . import hashtags_per_month
from . import join_leave_events_per_month
from . import mentions_per_user
from . import messages_by_weekday
from . import messages_per_hour
from . import messages_per_month
from . import pinned_messages_per_month
from . import ratio_service_vs_message_over_time
from . import top_users_by_messages_from_id
from . import topics_nmf
from . import wordcloud_top_words