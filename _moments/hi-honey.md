---
title: hi honey
date: 2024-10-23
date_display: c. 2024?
images:
  - file: hi-honey-random.webp
    alt: hi honey
  - file: hi-honey-layers.webp
    alt: hi honey (layers)
---
<pre class="moment-text">
Hi honey
i’m home
hope all is well
 
does being lonely
mean that I’m alone?
 
is this the right way?
does anyone here
know how to read a map?
 
i see meaning
in the slightest things
i have no idea what they mean
 
then I realise…
i’m staring at random dots
</pre>
{%- if page.images and page.images.size > 1 -%}
{%- assign img2 = page.images[1] -%}
<figure class="poem-hero">
  <img src="{{ '/assets/poems/img/' | append: img2.file | relative_url }}"
       alt="{{ img2.alt | default: page.title }}"
       loading="lazy" decoding="async">
  {%- if img2.caption -%}
    <figcaption>{{ img2.caption }}</figcaption>
  {%- endif -%}
</figure>
{%- endif -%}