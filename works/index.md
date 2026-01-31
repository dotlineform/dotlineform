---
layout: default
title: Works
permalink: /works/
section: works
---

{% assign works_items = site.works %}
{% if works_items and works_items != empty %}

  {% assign sorted_works = works_items | sort: 'work_id' | reverse %}

  <div class="index">
    <h1 class="index__heading">recent work</h1>

    {% for w in sorted_works limit: 6 %}
      {% include work_index_item work=w %}
    {% endfor %}
  </div>

{% else %}
  <p>no works yet</p>
{% endif %}
