---
layout: default
title: Themes
section: themes
permalink: /themes/
---

<h1 class="visually-hidden">Themes</h1>

<h2>Themes</h2>

{% assign themes = site.themes %}

{% if themes and themes != empty %}
  {% assign sorted_themes = themes | sort: 'date' | reverse %}
  <div class="index">
    {% for theme in sorted_themes %}
      {% if theme.published == false %}{% continue %}{% endif %}
      <div class="index__item">
        <span class="index__date">{% if theme.date %}{{ theme.date | date: "%-d %b %Y" }}{% endif %}</span>
        <a class="index__link" href="{{ theme.url | relative_url }}">{{ theme.title | default: theme.slug }}</a>
      </div>
    {% endfor %}
  </div>
{% else %}
  <p>No themes yet.</p>
{% endif %}