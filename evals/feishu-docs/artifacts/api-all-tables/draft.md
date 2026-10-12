# 工单查询接口说明

## 1 `get_ticket` — 工单查询

<table>
  <colgroup><col width="255" /><col width="765" /></colgroup>
  <thead><tr>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>项</b></p></th>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>说明</b></p></th>
  </tr></thead>
  <tbody>
    <tr>
      <td vertical-align="top"><p align="left">方法与路径</p></td>
      <td vertical-align="top"><p align="left">GET /v3/tickets/{id}</p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p align="left">认证</p></td>
      <td vertical-align="top"><p align="left">X-Client-Key 认证</p></td>
    </tr>
  </tbody>
</table>

**入参：**

<table>
  <colgroup><col width="255" /><col width="170" /><col width="595" /></colgroup>
  <thead><tr>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>字段</b></p></th>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>类型</b></p></th>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>说明</b></p></th>
  </tr></thead>
  <tbody><tr>
    <td vertical-align="top"><p align="left">id</p></td>
    <td vertical-align="top"><p align="left">integer</p></td>
    <td vertical-align="top"><p align="left">路径参数，必填</p></td>
  </tr></tbody>
</table>

**返回格式：** 沿用项目的 `ok/result` 响应契约，返回 `result` 中的工单标题，无分页。

`result`：

<table>
  <colgroup><col width="255" /><col width="170" /><col width="595" /></colgroup>
  <thead><tr>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>字段</b></p></th>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>类型</b></p></th>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>说明</b></p></th>
  </tr></thead>
  <tbody><tr>
    <td vertical-align="top"><p align="left">title</p></td>
    <td vertical-align="top"><p align="left">string</p></td>
    <td vertical-align="top"><p align="left">工单标题</p></td>
  </tr></tbody>
</table>

**返回示例：**

```json
{
  "ok": true,
  "result": {
    "title": "Test ticket"
  }
}
```

## 2 责任安排

<table>
  <colgroup><col width="255" /><col width="765" /></colgroup>
  <thead><tr>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>事项</b></p></th>
    <th background-color="light-gray" vertical-align="middle"><p align="center"><b>负责人</b></p></th>
  </tr></thead>
  <tbody><tr>
    <td vertical-align="top"><p align="left">联调</p></td>
    <td vertical-align="top"><p align="left">测试团队</p></td>
  </tr></tbody>
</table>
