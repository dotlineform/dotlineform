---
layout: default
title: Research
section: research
permalink: /research/
---

<h1 class="visually-hidden">Research</h1>

<h2>Research</h2>

{% assign research_items = site.research %}

{% if research_items and research_items != empty %}
  {% assign sorted_research = research_items | sort: 'date' | reverse %}
  <div class="index">

  {% for note in sorted_research %}
    {% if note.published == false %}{% continue %}{% endif %}
    <div class="index__item">
      <span class="index__date">{% if note.date %}{{ note.date | date: "%-d %b %Y" }}{% endif %}</span>
      <a class="index__link" href="{{ note.url | relative_url }}">{{ note.title | default: note.slug }}</a>
    </div>
  {% endfor %}

  </div>
{% else %}
  <p>No research notes yet.</p>
{% endif %}