<!-- slide bg="white" -->

<grid drag="100 6" drop="top" align="left" pad="0 20px" style="font-size: 16px;">
  <%? title %>
</grid>

<% content %>

<style>
.horizontal_dotted_line{
  border-bottom: 2px dotted gray;
}
</style>

<grid drag="94 0" drop="3 -6" class="horizontal_dotted_line">
</grid>

<grid drag="100 30" drop="0 64" align="bottomleft" pad="0 30px" style="font-size: 13px;" class="small-indent">
<%? source %>
</grid>

<grid drag="100 2" drop="bottom">
<p>Kemal Akkoyun | <a>https://kakkoyun.me</a></p>  <!-- element style="font-size: 16px;" class="small-indent" -->
</grid>
