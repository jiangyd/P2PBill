/**
 * Created by jyd on 2017/10/14.
 */
function arrayToJson(formArray) {
    var dataArray = {};
    $.each(formArray, function () {
        if (dataArray[this.name]) {
            if (!dataArray[this.name].push) {
                dataArray[this.name] = [dataArray[this.name]];
            }
            dataArray[this.name].push(this.value || '');
        } else {
            dataArray[this.name] = this.value || '';
        }
    });
    return JSON.stringify(dataArray);
}

$(document).on("click", "#mfa_code_submit", function () {
    // 获取请求地址
    var url = $("#mfa_code_submit").attr("url")
    var jsonobject = $("#formid").serializeArray();
    var v = arrayToJson(jsonobject)
    $.ajax({
        url: url,
        type: "POST",
        contentType: "application/json",
        data: v,
        success: function (data) {
            if (data.code == 0) {
                toastr.options.timeOut = 5000;
                toastr.success(data.msg)
                location.href = data.redirect;

            } else {
                toastr.options.timeOut = 3000;
                toastr.warning(data.msg)
            }
        }

    })
});

$(document).on("click", "#addbank_submit", function () {
    // 获取请求地址
    var url = $("#addbank_submit").attr("url")
    var jsonobject = $("#addbankform").serializeArray();
    var v = arrayToJson(jsonobject)
    $.ajax({
        url: url,
        type: "POST",
        contentType: "application/json",
        data: v,
        success: function (data) {
            if (data.code == 0) {
                $("#bankcard").modal('hide')
                toastr.options.timeOut = 5000;
                toastr.success(data.msg)


            } else {
                toastr.options.timeOut = 3000;
                toastr.warning(data.msg)
            }
        },
        error: function (textStatus) {
            $.each(textStatus.responseJSON.message, function (name, value) {
                toastr.options.timeOut = 3000;
                toastr.warning(value)
            });
        }

    })
});


$(document).on("click", "#modifybank_submit", function () {
    // 获取请求地址
    var url = $("#modifybank_submit").attr("url")
    var jsonobject = $("#modifybankform").serializeArray();
    var v = arrayToJson(jsonobject)
    $.ajax({
        url: url,
        type: "PUT",
        contentType: "application/json",
        data: v,
        success: function (data) {
            if (data.code == 0) {
                $("#modifybank").modal('hide')
                toastr.options.timeOut = 5000;
                toastr.success(data.msg)


            } else {
                toastr.options.timeOut = 3000;
                toastr.warning(data.msg)
            }
        },
        error: function (textStatus) {
            $.each(textStatus.responseJSON.message, function (name, value) {
                toastr.options.timeOut = 3000;
                toastr.warning(value)
            });
        }

    })
});