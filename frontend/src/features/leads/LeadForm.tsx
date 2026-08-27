import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { captureLead } from "@/api/leads";
import type { LeadCaptureRequest, CapturedLeadResponse } from "@/types/api";

const leadSchema = z.object({
  name: z.string().min(1, "Nome é obrigatório"),
  email: z.string().min(1, "Email é obrigatório").email("Email inválido"),
  phone: z
    .string()
    .optional()
    .refine(
      (val) => !val || /^\+?[\d\s()-]{8,20}$/.test(val),
      "Formato de telefone inválido",
    ),
  interest: z.string().optional(),
});

type LeadFormValues = z.infer<typeof leadSchema>;

interface LeadFormProps {
  onSuccess?: (lead: CapturedLeadResponse) => void;
}

export function LeadForm({ onSuccess }: LeadFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LeadFormValues>({
    resolver: zodResolver(leadSchema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      interest: "",
    },
  });

  const mutation = useMutation({
    mutationFn: (values: LeadFormValues) => {
      const payload: LeadCaptureRequest = {
        nome: values.name,
        email: values.email,
        telefone: values.phone || undefined,
        interesse: values.interest || undefined,
      };
      return captureLead(payload);
    },
    onSuccess: (lead) => {
      toast.success("Lead capturado com sucesso!");
      reset();
      onSuccess?.(lead);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Erro ao capturar lead");
    },
  });

  const onSubmit = (values: LeadFormValues) => {
    mutation.mutate(values);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Nome</Label>
        <Input
          id="name"
          placeholder="Nome completo"
          {...register("name")}
          aria-invalid={!!errors.name}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="email@exemplo.com"
          {...register("email")}
          aria-invalid={!!errors.email}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone">Telefone (opcional)</Label>
        <Input
          id="phone"
          type="tel"
          placeholder="+55 11 99999-0000"
          {...register("phone")}
          aria-invalid={!!errors.phone}
        />
        {errors.phone && (
          <p className="text-sm text-destructive">{errors.phone.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="interest">Interesse (opcional)</Label>
        <Input
          id="interest"
          placeholder="Ex: Produto X, Consultoria..."
          {...register("interest")}
        />
      </div>

      <Button type="submit" className="w-full" disabled={mutation.isPending}>
        {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {mutation.isPending ? "Capturando..." : "Capturar Lead"}
      </Button>
    </form>
  );
}
