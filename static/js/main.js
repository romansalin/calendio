moment.locale('en', {
  week: { dow: 1 }
});

$(function () {
    $('#datetimepicker12').datetimepicker({
        inline: true,
        sideBySide: true,
        format: 'dd.mm.yyyy HH:ii'
    });
});
