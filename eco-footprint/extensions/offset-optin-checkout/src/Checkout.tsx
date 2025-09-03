import {
  BlockStack,
  Checkbox,
  InlineStack,
  reactExtension,
  Text,
  useApplyAttributeChange,
  useApplyCartLinesChange,
  useCartLines,
  useCurrency,
  useSettings,
} from "@shopify/ui-extensions-react/checkout";

// 1. Choose an extension target
export default reactExtension(
  "purchase.checkout.reductions.render-after",
  () => <Extension />,
);

function Extension() {
  const currency = useCurrency();

  const cartLines = useCartLines();
  const applyCartLinesChange = useApplyCartLinesChange();
  const applyAttributeChange = useApplyAttributeChange();
  const {
    api_base = "https://localhost:8000",
    offset_variant_gid = "gid://shopify/ProductVariant/1234567890",
    label = "Offset Opt-In",
  } = useSettings() as {
    api_base: string;
    offset_variant_gid: string;
    label: string;
  };

  // compute subtotal from lines (shipping/taxes excluded)
  const subtotalCents = Math.round(
    cartLines.reduce((sum, l) => {
      // prefer total amount on the line; fallback to merchandise price * quantity
      const amt = Number(
        l.cost?.totalAmount?.amount ??
          (l.merchandise?.price?.amount ?? 0) * l.quantity,
      );
      return sum + amt * 100;
    }, 0),
  );

  const existing = cartLines.find(
    (l) =>
      l.merchandise?.id === offset_variant_gid &&
      (l.attributes || []).some(
        (a: any) => a?.key === "carbon_offset" && a?.value === "true",
      ),
  );
  const checked = Boolean(existing);

  async function onToggle(checked: boolean) {
    if (!offset_variant_gid || !api_base) return;

    // ask backend for estimate (2% placeholder)
    const est = await fetch(`${api_base}/v1/estimate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        shop: "foobar-pe",
        currency: currency.isoCode,
        items: [{ price_cents: subtotalCents, quantity: 1 }],
      }),
    }).then((r) => r.json());

    const unitCents = 1;
    const qty = Math.max(0, Math.round(est.estimate_cents / unitCents));

    if (checked) {
      if (existing) {
        await applyCartLinesChange({
          type: "updateCartLine",
          id: existing.id,
          quantity: qty,
        });
      } else {
        await applyCartLinesChange({
          type: "addCartLine",
          merchandiseId: offset_variant_gid,
          quantity: qty,
          attributes: [{ key: "carbon_offset", value: "true" }],
        });
      }

      await applyAttributeChange({
        type: "updateAttribute",
        key: "carbon_offset_opt_in",
        value: "yes",
      });
      await applyAttributeChange({
        type: "updateAttribute",
        key: "carbon_offset_cents",
        value: String(est.estimate_cents),
      });

      await fetch(`${api_base}/v1/opt-in`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          shop: "foobar-pe",
          cart_token: "1234567890",
          currency: currency.isoCode,
          subtotal_cents: est.subtotal_cents,
          estimate_cents: est.estimate_cents,
          payload: { source: "checkout-ui" },
        }),
      }).catch(() => {});
    } else {
      // remove
      if (existing) {
        await applyCartLinesChange({
          type: "removeCartLine",
          id: existing.id,
          quantity: existing.quantity,
        });
      }
      await applyAttributeChange({
        type: "updateAttribute",
        key: "carbon_offset_opt_in",
        value: "no",
      });
      await applyAttributeChange({
        type: "updateAttribute",
        key: "carbon_offset_cents",
        value: "0",
      });
    }
  }

  return (
    <BlockStack spacing="tight">
      <InlineStack spacing="tight" blockAlignment="center">
        <Checkbox
          id="carbon-offset"
          checked={checked}
          onChange={onToggle}
          accessibilityLabel={label || "Reduce my order’s carbon footprint"}
        >
          {label || "Reduce my order’s carbon footprint"}
        </Checkbox>
      </InlineStack>
      {!checked ? (
        <Text appearance="subdued">
          Estimated offset on this order is ~{" "}
          {formatMoney(currency.isoCode.toString(), subtotalCents * 0.02)}
        </Text>
      ) : (
        <Text emphasis="bold">Carbon offset will be added to your order.</Text>
      )}
    </BlockStack>
  );
}

function formatMoney(currency: string, cents: number) {
  const amount = (cents || 0) / 100;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(amount);
}
