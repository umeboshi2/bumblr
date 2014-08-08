# modular template loading
define (require, exports, module) ->
  $ = require 'jquery'
  _ = require 'underscore'
  Backbone = require 'backbone'

  marked = require 'marked'
  
  teacup = require 'teacup'

  renderable = teacup.renderable

  div = teacup.div
  # I use "icon" for font-awesome
  icon = teacup.i
  strong = teacup.strong
  span = teacup.span
  label = teacup.label
  input = teacup.input

  text = teacup.text
  img = teacup.img
  # Main Templates must use teacup.
  # The template must be a teacup.renderable, 
  # and accept a layout model as an argument.

  # Tagnames to be used in the template.
  {div, span, link, text, strong, label, input, 
  button, a, nav, form, p,
  ul, li, b,
  h1, h2, h3,
  subtitle, section, hr
  } = teacup
            
  capitalize = (str) ->
    str.charAt(0).toUpperCase() + str.slice(1)

  handle_newlines = (str) ->
   str.replace(/(?:\r\n|\r|\n)/g, '<br />')
    
  ########################################
  # Templates
  ########################################
  sidebar = renderable (model) ->
    div '.listview-list.btn-group-vertical', ->
      for entry in model.entries
        div '.btn.btn-default.' + entry.name, entry.label
        
  meeting_calendar = renderable () ->
    div '.listview-header', 'Meetings'
    div '#loading', ->
      h2 'Loading Meetings'
    div '#maincalendar'

  main_bumblr_view = renderable (model) ->
    p 'main bumblr view'

  bumblr_dashboard_view = renderable (model) ->
    p 'bumblr_dashboard_view'


  simple_blog_info = renderable (blog) ->
    div ->
      a href:'#demo/viewblog/' + blog.name, blog.name

  simple_post_view = renderable (post) ->
    span ->
      a href:post.post_url, target:'_blank', post.blog_name
    span ->
      for photo in post.photos
        for size in photo.alt_sizes
          if size.width == 400
            img src:size.url, href:post.url
  ##################################################################
  # ##########################
  ##################################################################    
          
  module.exports =
    sidebar: sidebar
    meeting_calendar: meeting_calendar
    main_bumblr_view: main_bumblr_view
    bumblr_dashboard_view: bumblr_dashboard_view
    simple_blog_info: simple_blog_info
    simple_post_view: simple_post_view
    
    