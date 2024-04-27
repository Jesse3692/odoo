from odoo import api, exceptions, fields, models, tools


import datetime


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "offer of estate property"
    _order = "price desc"

    price = fields.Float()
    status = fields.Selection(
        string="offer status",  # 报价状态
        selection=[("accepted", "Accepted"), ("refused", "Refused")],
        help="Offer status is used to show the offer's status",
        copy=False,  # 复制记录时不复制此字段
    )
    partner_id = fields.Many2one("res.partner", string="Partner", required=True)  # noqa:E501
    property_id = fields.Many2one("estate.property", required=True)
    validity = fields.Integer(default=7)  # 报价有效期，默认7天
    date_deadline = fields.Date(
        compute="_compute_date_deadline", inverse="_inverse_date_deadline"
    )  # 报价截止日期
    property_type_id = fields.Many2one(
        related="property_id.property_type_id", store=True
    )  # 房产类型

    # 约束
    _sql_constraints = [
        ("check_price", "CHECK (price > 0)", "An offer price must be strictly positive")  # noqa:E501
    ]

    # 计算报价截至日期
    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        for record in self:
            # 如果有创建日期，则使用创建日期，否则使用当前日期
            start_date = (
                record.create_date if record.create_date else datetime.date.today()  # noqa:E501
            )
            record.date_deadline = start_date + datetime.timedelta(days=record.validity)  # noqa:E501

    # 重置报价截至日期的反向方法
    def _inverse_date_deadline(self):
        for record in self:
            record.validity = (record.date_deadline - record.create_date.date()).days

    # 接受报价
    def action_accept(self):
        for record in self:
            # 重置房产的所有报价状态
            self._reset_offers_status(record.property_id)
            # 设置当前报价状态为接受
            record.status = "accepted"
            # 更新房产的销售价格和买家
            record.property_id.selling_price = record.price
            record.property_id.partner_id = record.partner_id
            # 更新房产的状态为已接受报价
            record.property_id.state = "accepted"
        return True

    # 拒绝报价
    def action_refuse(self):
        for record in self:
            # 如果报价为接受状态，则重置房产的报价状态
            if record.status == "accepted":
                self._reset_property_id(record)
            # 设置当前报价状态为拒绝
            record.status = "refused"
            # 更新房产的状态为已收到报价
            record.property_id.state = "received"
        return True

    # 重置房产的所有报价状态
    def _reset_offers_status(self, property_id):
        for record in property_id.offer_ids:
            if record.status == "accepted":
                record.status = "refused"

    # 重置房产报价
    def _reset_property_id(self, record):
        record.property_id.selling_price = 0
        record.property_id.partner_id = None

    # 重写创建方法
    @api.model
    def create(self, vals):
        # 获取房产记录
        estate_property = self.env["estate.property"].browse(vals["property_id"])  # noqa:E501
        # 如果报价不高于最佳报价
        if (
            tools.float_compare(
                estate_property.best_price, vals["price"], precision_digits=3
            )
            >= 0
        ):
            raise exceptions.UserError(
                "The offer must be higher than $%.2f" % estate_property.best_price  # noqa:E501
            )
        # 更新房产状态为已收到报价
        estate_property.state = "received"
        # 调用父类的创建方法
        return super().create(vals)
