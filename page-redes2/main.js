$(document).ready(function() {
    $(function(){
        $('.targetDiv').hide();
        $('.botoes').hide();
        $('.active').click(function(){
            $('.targetDiv').hide();
            $('.botoes').hide();
            $("#titulo").show();
        });

        $('.showSingle').click(function(){
              $("#titulo").hide();
              $('.targetDiv').hide();
              $('.botoes').show();
              $('#div'+$(this).attr('target')).show();
        });
    });
});
