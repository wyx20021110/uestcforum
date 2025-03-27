from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """从字典中获取指定键的值，用于模板中访问字典数据"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """乘法过滤器"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """除法过滤器"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0 