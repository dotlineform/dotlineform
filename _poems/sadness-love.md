---
title: sadness love
date: 2010-1-23
images:
  - file: sadness-love-fog.webp
    alt: sadness love (fog)
  - file: sadness-love.webp
    alt: sadness love
    caption: blue sky for Pebble, rest in peace 23 Jan 2010
---
<pre class="poem-text">
sadness permeates this world, infuses it like a fog. philosophy abstracts it, turns it into a property of language, invents names for it. but there is no way to escape it by understanding how it is defined because it has no substance, nothing you can take hold of and mold. belief comes closer, in seeing sadness as something real but by the grace of God also something from somewhere else, as if it is a divine property that is put upon us to be embraced and absorbed, so that we can be forgiven. but there is no way to release grief in guilt, forgive ourselves for something that we cannot separate out because it is an irreducible part of our lives.
 
like memories, bindweed, sadness has presence but no place, no fixed abode. it seeps through our past and future, sleeps in our pores, rises up deafeningly from the depths and then returns silently like a liquid flowing easily over impossibly jagged surfaces. perhaps then we can use it like all natural things that are able to live in inhospitable places, for medicinal purposes, to heal. sadness changes things, it changes everything, and so therefore it has great strength. sadness and hope, wishes, they are real.
 
single moments are always cruel because we cannot perceive them for what they really are, they just stab us and instantly leave us with confused fragments. but our love for lives that are no longer with us, in a cruel present that we grasp to feel but never find peace in, extends into our past and future, and so is outside of the passing of time, a peaceful eternal.

{% if page.images and page.images.size > 1 %}
  {% assign img2 = page.images[1] %}
  <figure class="poem-hero">
    <img src="{{ '/assets/poems/img/' | append: img2.file | relative_url }}"
         alt="{{ img2.alt | default: page.title }}"
         loading="lazy" decoding="async">
    {% if img2.caption %}
      <figcaption>{{ img2.caption }}</figcaption>
    {% endif %}
  </figure>
{% endif %}
</pre>