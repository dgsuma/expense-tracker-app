import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/auth_controller.dart';
import '../../core/data_providers.dart';
import '../../core/models.dart';

class ExpenseForm extends ConsumerStatefulWidget {
  final Expense? expense;
  const ExpenseForm({super.key, this.expense});

  @override
  ConsumerState<ExpenseForm> createState() => _ExpenseFormState();
}

class _ExpenseFormState extends ConsumerState<ExpenseForm> {
  final _formKey = GlobalKey<FormState>();
  late final _descriptionController =
      TextEditingController(text: widget.expense?.description ?? '');
  late final _amountController =
      TextEditingController(text: widget.expense?.amount ?? '');
  late final _notesController =
      TextEditingController(text: widget.expense?.notes ?? '');
  String? _categoryId;
  String? _paymentMethodId;
  late DateTime _date = widget.expense?.expenseDate ?? DateTime.now();
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _categoryId = widget.expense?.categoryId;
    _paymentMethodId = widget.expense?.paymentMethodId;
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    _amountController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    if (_categoryId == null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Select a category')));
      return;
    }
    setState(() => _saving = true);
    final api = ref.read(apiClientProvider);
    final data = {
      'category_id': _categoryId,
      'payment_method_id': _paymentMethodId,
      'amount': double.parse(_amountController.text),
      'currency': 'EUR',
      'expense_date': DateFormat('yyyy-MM-dd').format(_date),
      'description': _descriptionController.text.trim(),
      'notes': _notesController.text.trim().isEmpty
          ? null
          : _notesController.text.trim(),
    };
    try {
      if (widget.expense == null) {
        await api.dio.post('/api/v1/expenses', data: data);
      } else {
        await api.dio
            .patch('/api/v1/expenses/${widget.expense!.id}', data: data);
      }
      ref.invalidate(expensesProvider);
      ref.invalidate(summaryProvider);
      ref.invalidate(categoryTotalsProvider);
      ref.invalidate(trendsProvider);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Failed to save: $e')));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final categories = ref.watch(categoriesProvider);
    final paymentMethods = ref.watch(paymentMethodsProvider);

    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 16,
        right: 16,
        top: 16,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                widget.expense == null ? 'Add expense' : 'Edit expense',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _descriptionController,
                decoration: const InputDecoration(labelText: 'Description'),
                validator: (v) =>
                    v != null && v.isNotEmpty ? null : 'Enter a description',
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _amountController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'Amount'),
                validator: (v) {
                  final parsed = double.tryParse(v ?? '');
                  if (parsed == null || parsed <= 0)
                    return 'Enter a valid amount';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              categories.when(
                loading: () => const LinearProgressIndicator(),
                error: (e, _) => Text('Failed to load categories: $e'),
                data: (cats) {
                  final options = <DropdownMenuItem<String>>[];
                  for (final c in cats) {
                    options.add(
                        DropdownMenuItem(value: c.id, child: Text(c.name)));
                    for (final sub in c.children) {
                      options.add(DropdownMenuItem(
                          value: sub.id,
                          child: Text('  ${c.name} › ${sub.name}')));
                    }
                  }
                  return DropdownButtonFormField<String>(
                    initialValue: _categoryId,
                    decoration: const InputDecoration(labelText: 'Category'),
                    items: options,
                    onChanged: (v) => setState(() => _categoryId = v),
                  );
                },
              ),
              const SizedBox(height: 12),
              paymentMethods.when(
                loading: () => const SizedBox.shrink(),
                error: (_, __) => const SizedBox.shrink(),
                data: (methods) => DropdownButtonFormField<String>(
                  initialValue: _paymentMethodId,
                  decoration: const InputDecoration(
                      labelText: 'Payment method (optional)'),
                  items: [
                    const DropdownMenuItem(value: null, child: Text('None')),
                    ...methods.map((m) =>
                        DropdownMenuItem(value: m.id, child: Text(m.name))),
                  ],
                  onChanged: (v) => setState(() => _paymentMethodId = v),
                ),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                icon: const Icon(Icons.calendar_today),
                label: Text(DateFormat.yMMMd().format(_date)),
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: _date,
                    firstDate: DateTime(2000),
                    lastDate: DateTime(2100),
                  );
                  if (picked != null) setState(() => _date = picked);
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _notesController,
                decoration:
                    const InputDecoration(labelText: 'Notes (optional)'),
                maxLines: 2,
              ),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: _saving ? null : _save,
                child: _saving
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : Text(widget.expense == null ? 'Add' : 'Save'),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}
