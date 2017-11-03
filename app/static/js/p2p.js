/**
 * Created by jyd on 2017/10/14.
 */

function arrayToJson(formArray){
  var dataArray = {};
  $.each(formArray,function(){
    if(dataArray[this.name]){
      if(!dataArray[this.name].push){
        dataArray[this.name] = [dataArray[this.name]];
      }
      dataArray[this.name].push(this.value || '');
    }else{
      dataArray[this.name] = this.value || '';
    }
  });
  return JSON.stringify(dataArray);
}

$(document).on("click","#mfa_code_submit",function () {
    // 获取请求地址
    var url=$("#mfa_code_submit").attr("url")
    //获取code内容
    var code=$("#code").val()
    var jsonobject=$("#formid").serializeArray();
    var v=arrayToJson(jsonobject)
    $.ajax({
        url:url,
        type:"POST",
        contentType:"application/json",
        data:v,
        success:function (data) {
            if(data.code==0){
                toastr.options.timeOut = 5000;
                toastr.success(data.msg)
                location.href=data.redirect;

            }else{
                toastr.options.timeOut = 3000;
                toastr.warning(data.msg)
            }
        }

    })
})