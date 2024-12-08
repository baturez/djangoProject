from django import template
import re

register = template.Library()

@register.filter
def get_object_id(request):
    return str(request.get('_id')) if '_id' in request else None

@register.filter
def regex_search(value, pattern):
    """Returns True if the regex pattern matches the value, else False."""
    return bool(re.search(pattern, value))
@register.filter
def get_post_id(post):
    """Returns the post ID as a string."""
    return str(post.get('_id')) if '_id' in post else None
@register.filter
def get_comment_id(comment):
    """Returns the comment ID as a string."""
    return str(comment.get('_id')) if '_id' in comment else None

@register.filter
def round_to(value, decimals=2):
    """Rounds a number to the specified decimal places. Default is 2 decimals."""
    try:
        return round(float(value), decimals)
    except (ValueError, TypeError):
        return value