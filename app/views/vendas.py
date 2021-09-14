from .imports import *
from .general import *
 
def vendas(request, pk):
    data = {}
    data['db'] = Funcionario.objects.get(pk=pk)
    data['venda_form'] = VendaForm()
    return render(request, 'vendas/nova_venda.html', data)


def nova_venda(request, pk):
    user = Funcionario.objects.get(pk=pk)
    form = VendaForm(request.POST or None)
    today  = pendulum.today()
    #DADOS QUE VÊM DO FORMULARIO
    if form.is_valid():  #VERIFICA SE TUDO É VÁLIDO
        instance = form.save()
        instance.funcionario_id = pk
        instance.is_active = True
        instance.is_paid = False

        calculo_comissao = (instance.valor_venda * (user.comissao / 100))
        total = user.total_a_receber + calculo_comissao

        instance.mes_venda = int(today.month)


        Funcionario.objects.filter(pk=pk).update(total_a_receber=total)

        instance.save()

        return redirect('home')  #*REDIRECIONA PARA A HOME


def listar_vendas(request, pk):
    user = Funcionario.objects.get(pk=pk)

    proximo_mes= int(user.data_pagamento.month)
    #Atualiza os que já foram pagos
    query = (Q(funcionario_id=pk) & Q(mes_venda__lte=proximo_mes))

    if user.mes_pago:
        Venda.objects.filter(query).update(is_paid=True)

    queryset = Venda.objects.all()

    #* SOMA TODOS AS VENDAS DO FUNCIONARIO, MULTIPLICA PELA TAXA DE COMISSAO E RETORNA O RESULTADO
    total_comissao = list(
        Venda.objects.filter(funcionario_id__exact=pk).aggregate(
            Sum('valor_venda')).values())[0] * (user.comissao / 100)

    context = {
        "user": user,
        "object_list": queryset,
        "total_comissao": total_comissao
    }

    return render(request, 'vendas/listar_vendas.html', context)


def remover_pagamento_comissao(funcionario_id, pk):
    instance = Venda.objects.get(pk=pk)
    user = Funcionario.objects.get(pk=funcionario_id)
    user.total_a_receber -= (instance.valor_venda * (user.comissao / 100))
    Funcionario.objects.filter(pk=funcionario_id).update(
        total_a_receber=user.total_a_receber)


def inserir_pagamento_comissao(funcionario_id, pk):
    instance = Venda.objects.get(pk=pk)
    user = Funcionario.objects.get(pk=funcionario_id)
    user.total_a_receber += (instance.valor_venda * (user.comissao / 100))
    Funcionario.objects.filter(pk=funcionario_id).update(
        total_a_receber=user.total_a_receber)


def desativar_venda(request, funcionario_id, pk):

    funcionario = Funcionario.objects.get(pk=funcionario_id)
    instance = Venda.objects.get(pk=pk)
    remover_pagamento_comissao(funcionario_id, pk)
    Venda.objects.filter(pk=pk).update(is_active=False)
    return listar_vendas(request, funcionario_id)


def reativar_venda(request, funcionario_id, pk):
    inserir_pagamento_comissao(funcionario_id, pk)
    Venda.objects.filter(pk=pk).update(is_active=True)
    return listar_vendas(request, funcionario_id)

