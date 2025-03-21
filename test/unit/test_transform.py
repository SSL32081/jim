import jax
import jax.numpy as jnp

from jimgw.transforms import (
    ScaleTransform,
    OffsetTransform,
    LogitTransform,
    SineTransform,
    CosineTransform,
    BoundToBound,
    BoundToUnbound,
    SingleSidedUnboundTransform,
    PowerLawTransform,
    reverse_bijective_transform,
)
from jimgw.single_event.transforms import SpinAnglesToCartesianSpinTransform
from jimgw.single_event.utils import m1_m2_to_Mc_q

import numpy as np

jax.config.update("jax_enable_x64", True)


class TestBasicTransforms:
    def test_scale_transform(self):
        name_mapping = (["a", "b"], ["a_scaled", "b_scaled"])
        scale = 3.0
        transform = ScaleTransform(name_mapping, scale)
        input_data = {"a": 2.0, "b": 4.0}

        # Test forward transformation
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(list(output.values()), [2.0 * scale, 4.0 * scale])
        assert np.allclose(log_det, 2 * jnp.log(scale))

        # Test inverse transformation
        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(list(recovered.values()), list(input_data.values()))
        assert np.allclose(inv_log_det, -2 * jnp.log(scale))

        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))

        # Test jitted forward transformation
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(list(jitted_output.values()), [2.0 * scale, 4.0 * scale])
        assert np.allclose(jitted_log_det, 2 * jnp.log(scale))

        # Test jitted inverse transformation
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(list(jitted_recovered.values()), list(input_data.values()))
        assert np.allclose(jitted_inv_log_det, -2 * jnp.log(scale))

    def test_offset_transform(self):
        name_mapping = (["x", "y"], ["x_offset", "y_offset"])
        offset = 5.0
        transform = OffsetTransform(name_mapping, offset)
        input_data = {"x": 10.0, "y": -3.0}

        # Test forward transformation
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(list(output.values()), [10.0 + offset, -3.0 + offset])
        assert np.allclose(log_det, 0.0)

        # Test inverse transformation
        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(list(recovered.values()), list(input_data.values()))
        assert np.allclose(inv_log_det, 0.0)

        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))

        # Test jitted forward transformation
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(list(jitted_output.values()), [10.0 + offset, -3.0 + offset])
        assert np.allclose(jitted_log_det, 0.0)

        # Test jitted inverse transformation
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(list(jitted_recovered.values()), list(input_data.values()))
        assert np.allclose(jitted_inv_log_det, 0.0)

    def test_logit_transform(self):
        name_mapping = (["p"], ["p_logit"])
        transform = LogitTransform(name_mapping)
        input_data = {"p": 0.6}

        # Test forward transformation
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(output["p_logit"], 1 / (1 + jnp.exp(-0.6)))
        assert np.isfinite(log_det)

        # Test inverse transformation
        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(recovered["p"], input_data["p"])
        assert np.isfinite(inv_log_det)

        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))

        # Test jitted forward transformation
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(jitted_output["p_logit"], 1 / (1 + jnp.exp(-0.6)))
        assert np.isfinite(jitted_log_det)

        # Test jitted inverse transformation
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(jitted_recovered["p"], input_data["p"])
        assert np.isfinite(jitted_inv_log_det)

    def test_sine_transform(self):
        name_mapping = (["theta"], ["sin_theta"])
        transform = SineTransform(name_mapping)
        angle = 0.3
        input_data = {"theta": angle}

        # Test forward transformation
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(output["sin_theta"], jnp.sin(angle))
        assert np.allclose(log_det, jnp.log(jnp.abs(jnp.cos(angle))))

        # Test inverse transformation
        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(recovered["theta"], angle)
        assert np.allclose(inv_log_det, -jnp.log(jnp.abs(jnp.cos(angle))))

        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))

        # Test jitted forward transformation
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(jitted_output["sin_theta"], jnp.sin(angle))
        assert np.allclose(jitted_log_det, jnp.log(jnp.abs(jnp.cos(angle))))

        # Test jitted inverse transformation
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(jitted_recovered["theta"], angle)
        assert np.allclose(jitted_inv_log_det, -jnp.log(jnp.abs(jnp.cos(angle))))

    def test_cosine_transform(self):
        name_mapping = (["theta"], ["cos_theta"])
        transform = CosineTransform(name_mapping)
        angle = 1.2
        input_data = {"theta": angle}

        # Test forward transformation
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(output["cos_theta"], jnp.cos(angle))
        assert np.isfinite(log_det)

        # Test inverse transformation
        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(recovered["theta"], angle)
        assert np.isfinite(inv_log_det)

        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))

        # Test jitted forward transformation
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(jitted_output["cos_theta"], jnp.cos(angle))
        assert np.isfinite(jitted_log_det)

        # Test jitted inverse transformation
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(jitted_recovered["theta"], angle)
        assert np.isfinite(jitted_inv_log_det)

    def test_bound_to_bound(self):
        # Transform a value from an original range [0, 10] to a target range [100, 200].
        name_mapping = (["x"], ["x_mapped"])
        orig_lower = jnp.array([0.0])
        orig_upper = jnp.array([10.0])
        target_lower = jnp.array([100.0])
        target_upper = jnp.array([200.0])
        transform = BoundToBound(
            name_mapping, orig_lower, orig_upper, target_lower, target_upper
        )
        input_data = {"x": 5.0}  # mid-point of original range

        # Expected: (5-0)*(200-100)/(10-0) + 100 = 150
        expected_forward = 150.0
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(output["x_mapped"], expected_forward)
        # For one dimension, derivative is constant:
        expected_log_det = jnp.log(
            (target_upper - target_lower) / (orig_upper - orig_lower)
        )
        assert np.allclose(log_det, expected_log_det)

        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(recovered["x"], input_data["x"])
        assert np.allclose(inv_log_det, -expected_log_det)

        # JIT compiled version
        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(jitted_output["x_mapped"], expected_forward)
        assert np.allclose(jitted_log_det, expected_log_det)
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(jitted_recovered["x"], input_data["x"])
        assert np.allclose(jitted_inv_log_det, -expected_log_det)

    def test_bound_to_unbound(self):
        # Transform a value from a bounded interval [0, 1] to an unbounded domain.
        name_mapping = (["p"], ["p_unbound"])
        transform = BoundToUnbound(name_mapping, 0.0, 1.0)
        input_data = {"p": 0.5}
        # Expected forward: logit((0.5-0)/(1-0)) = log(0.5/0.5) = 0.
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(output["p_unbound"], 0.0)
        assert np.isfinite(log_det)

        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(recovered["p"], 0.5)
        assert np.isfinite(inv_log_det)

        # JIT compiled
        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(jitted_output["p_unbound"], 0.0)
        assert np.isfinite(jitted_log_det)
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(jitted_recovered["p"], 0.5)
        assert np.isfinite(jitted_inv_log_det)

    def test_single_sided_unbound_transform(self):
        # Test a transform that maps from a lower-bound-limited input to an unbounded output.
        name_mapping = (["x"], ["x_unbound"])
        lower_bound = 10.0
        transform = SingleSidedUnboundTransform(name_mapping, lower_bound)
        input_data = {"x": 20.0}
        expected_forward = jnp.log(20.0 - lower_bound)  # log(10)
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(output["x_unbound"], expected_forward)
        assert np.isfinite(log_det)

        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(recovered["x"], 20.0)
        assert np.isfinite(inv_log_det)

        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(jitted_output["x_unbound"], expected_forward)
        assert np.isfinite(jitted_log_det)
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(jitted_recovered["x"], 20.0)
        assert np.isfinite(jitted_inv_log_det)

    def test_powerlaw_transform(self):
        # Test the branch with alpha == -1.0.
        name_mapping = (["x"], ["x_powerlaw"])
        xmin = 1.0
        xmax = 10.0
        alpha = -1.0
        transform = PowerLawTransform(name_mapping, xmin, xmax, alpha)
        # For input x, forward transform: xmin * exp(x * ln(xmax/xmin)).
        input_data = {"x": 0.5}
        expected_forward = xmin * jnp.exp(0.5 * jnp.log(xmax / xmin))
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(output["x_powerlaw"], expected_forward)
        assert np.isfinite(log_det)

        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(recovered["x"], 0.5)
        assert np.isfinite(inv_log_det)

        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(jitted_output["x_powerlaw"], expected_forward)
        assert np.isfinite(jitted_log_det)
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(jitted_recovered["x"], 0.5)
        assert np.isfinite(jitted_inv_log_det)

    def test_powerlaw_transformn(self):
        # Test the branch with alpha != -1.0 (e.g. alpha = 1.0).
        name_mapping = (["x"], ["x_powerlaw"])
        xmin = 1.0
        xmax = 10.0
        alpha = 1.0
        transform = PowerLawTransform(name_mapping, xmin, xmax, alpha)
        # For input x, forward transform:
        # output = (xmin^(1+alpha) + x*(xmax^(1+alpha) - xmin^(1+alpha)))^(1/(1+alpha))
        input_data = {"x": 0.5}
        inner = xmin ** (1.0 + alpha) + 0.5 * (
            xmax ** (1.0 + alpha) - xmin ** (1.0 + alpha)
        )
        expected_forward = inner ** (1.0 / (1.0 + alpha))
        output, log_det = transform.transform(input_data.copy())
        assert np.allclose(output["x_powerlaw"], expected_forward)
        assert np.isfinite(log_det)

        recovered, inv_log_det = transform.inverse(output.copy())
        assert np.allclose(recovered["x"], input_data["x"])
        assert np.isfinite(inv_log_det)

        jit_transform = jax.jit(lambda x: transform.transform(x))
        jit_inverse = jax.jit(lambda x: transform.inverse(x))
        jitted_output, jitted_log_det = jit_transform(input_data)
        assert np.allclose(jitted_output["x_powerlaw"], expected_forward)
        assert np.isfinite(jitted_log_det)
        jitted_recovered, jitted_inv_log_det = jit_inverse(jitted_output)
        assert np.allclose(jitted_recovered["x"], input_data["x"])
        assert np.isfinite(jitted_inv_log_det)


class TestSpinTransform:
    forward_keys = (
        "theta_jn",
        "phi_jl",
        "tilt_1",
        "tilt_2",
        "phi_12",
        "a_1",
        "a_2",
        "M_c",
        "q",
        "phase_c",
    )

    backward_keys = (
        "iota",
        "s1_x",
        "s1_y",
        "s1_z",
        "s2_x",
        "s2_y",
        "s2_z",
        "M_c",
        "q",
        "phase_c",
    )

    def test_forward_spin_transform(self):
        """
        Test transformation from spin angles to cartesian spins

        Input and output values are generated with bilby_spin.py
        """

        # read inputs from binary
        inputs = jnp.load("test/unit/source_files/spin_angles_input.npz")
        inputs = [inputs[key] for key in inputs.keys()]
        M_c, q = m1_m2_to_Mc_q(inputs[7], inputs[8])

        # read outputs from binary
        bilby_spins = jnp.load(
            "test/unit/source_files/cartesian_spins_output_for_bilby.npz"
        )
        bilby_spins = jnp.array([bilby_spins[key] for key in bilby_spins.keys()]).T

        n = 100  # max: 100

        # compute jimgw spins
        for i in range(n):
            row = [
                inputs[0][i],
                inputs[1][i],
                inputs[2][i],
                inputs[3][i],
                inputs[4][i],
                inputs[5][i],
                inputs[6][i],
                M_c[i],
                q[i],
                inputs[10][i],
            ]

            freq_ref = inputs[9][i]

            jimgw_spins, jacobian = SpinAnglesToCartesianSpinTransform(
                freq_ref=freq_ref
            ).transform(dict(zip(self.forward_keys, row)))

            for key in ("M_c", "q", "phase_c"):
                jimgw_spins.pop(key)

            assert jnp.allclose(jnp.array(list(jimgw_spins.values())), bilby_spins[i])
            # default atol: 1e-8, rtol: 1e-5
            assert not jnp.isnan(jacobian).any()

    def test_backward_spin_transform(self):
        """
        Test transformation from cartesian spins to spin angles

        Input and output values are generated with bilby_spin.py
        """

        # read inputs from binary
        inputs = jnp.load("test/unit/source_files/cartesian_spins_input.npz")
        inputs = [inputs[key] for key in inputs.keys()]
        M_c, q = m1_m2_to_Mc_q(inputs[7], inputs[8])

        # read outputs from binary
        bilby_spins = jnp.load(
            "test/unit/source_files/spin_angles_output_for_bilby.npz"
        )
        bilby_spins = jnp.array([bilby_spins[key] for key in bilby_spins.keys()]).T

        n = 100  # max: 100

        # compute jimgw spins
        for i in range(n):
            row = [
                inputs[0][i],
                inputs[1][i],
                inputs[2][i],
                inputs[3][i],
                inputs[4][i],
                inputs[5][i],
                inputs[6][i],
                M_c[i],
                q[i],
                inputs[10][i],
            ]

            freq_ref = inputs[9][i]

            jimgw_spins, jacobian = SpinAnglesToCartesianSpinTransform(
                freq_ref=freq_ref
            ).inverse(dict(zip(self.backward_keys, row)))

            for key in ("M_c", "q", "phase_c"):
                jimgw_spins.pop(key)
            jimgw_spins = list(jimgw_spins.values())

            assert jnp.allclose(jnp.array(jimgw_spins), bilby_spins[i])
            # default atol: 1e-8, rtol: 1e-5
            assert not jnp.isnan(jacobian).any()

    def test_forward_backward_consistency(self):
        """
        Test that the forward and inverse transformations are consistent
        """

        n = 10

        key = jax.random.PRNGKey(42)
        for _ in range(n):
            key, subkey = jax.random.split(key)
            subkeys = jax.random.split(subkey, 5)
            iota = jax.random.uniform(subkeys[0], (1,), minval=0, maxval=jnp.pi)
            M_c = jax.random.uniform(subkeys[1], (1,), minval=1, maxval=100)
            q = jax.random.uniform(subkeys[2], (1,), minval=0.125, maxval=1)
            fRef = jax.random.uniform(subkeys[3], (1,), minval=10, maxval=100)
            phiRef = jax.random.uniform(subkeys[4], (1,), minval=0, maxval=2 * jnp.pi)

            while True:
                key, subkey = jax.random.split(key)
                subkeys = jax.random.split(subkey, 6)
                S1x = jax.random.uniform(subkeys[0], (1,), minval=-1, maxval=1)
                S1y = jax.random.uniform(subkeys[1], (1,), minval=-1, maxval=1)
                S1z = jax.random.uniform(subkeys[2], (1,), minval=-1, maxval=1)
                S2x = jax.random.uniform(subkeys[3], (1,), minval=-1, maxval=1)
                S2y = jax.random.uniform(subkeys[4], (1,), minval=-1, maxval=1)
                S2z = jax.random.uniform(subkeys[5], (1,), minval=-1, maxval=1)
                if (
                    jnp.linalg.norm(jnp.array([S1x[0], S1y[0], S1z[0]])) <= 1
                    and jnp.linalg.norm(jnp.array([S2x[0], S2y[0], S2z[0]])) <= 1
                ):
                    break

            sample = [
                iota[0],
                S1x[0],
                S1y[0],
                S1z[0],
                S2x[0],
                S2y[0],
                S2z[0],
                M_c[0],
                q[0],
                phiRef[0],
            ]

            jimgw_spins, _ = SpinAnglesToCartesianSpinTransform(
                freq_ref=fRef[0]
            ).inverse(dict(zip(self.backward_keys, sample)))
            jimgw_spins, _ = SpinAnglesToCartesianSpinTransform(
                freq_ref=fRef[0]
            ).transform(jimgw_spins)
            jimgw_spins = list(jimgw_spins.values())
            assert jnp.allclose(
                jnp.array(jimgw_spins), jnp.array([*sample[7:], *sample[:7]])
            )
            # default atol: 1e-8, rtol: 1e-5

    def test_jitted_forward_transform(self):
        """
        Test that the forward transformation is JIT compilable
        """

        # Generate random sample
        subkeys = jax.random.split(jax.random.PRNGKey(12), 6)
        iota = jax.random.uniform(subkeys[0], (1,), minval=0, maxval=jnp.pi)
        M_c = jax.random.uniform(subkeys[1], (1,), minval=1, maxval=100)
        q = jax.random.uniform(subkeys[2], (1,), minval=0.125, maxval=1)
        fRef = jax.random.uniform(subkeys[3], (1,), minval=10, maxval=100)
        phiRef = jax.random.uniform(subkeys[4], (1,), minval=0, maxval=2 * jnp.pi)

        key = subkeys[5]
        while True:
            key, subkey = jax.random.split(key)
            subkeys = jax.random.split(subkey, 6)
            S1x = jax.random.uniform(subkeys[0], (1,), minval=-1, maxval=1)
            S1y = jax.random.uniform(subkeys[1], (1,), minval=-1, maxval=1)
            S1z = jax.random.uniform(subkeys[2], (1,), minval=-1, maxval=1)
            S2x = jax.random.uniform(subkeys[3], (1,), minval=-1, maxval=1)
            S2y = jax.random.uniform(subkeys[4], (1,), minval=-1, maxval=1)
            S2z = jax.random.uniform(subkeys[5], (1,), minval=-1, maxval=1)
            if (
                jnp.linalg.norm(jnp.array([S1x[0], S1y[0], S1z[0]])) <= 1
                and jnp.linalg.norm(jnp.array([S2x[0], S2y[0], S2z[0]])) <= 1
            ):
                break

        sample = [
            iota[0],
            S1x[0],
            S1y[0],
            S1z[0],
            S2x[0],
            S2y[0],
            S2z[0],
            M_c[0],
            q[0],
            phiRef[0],
        ]
        freq_ref_sample = fRef[0]
        sample_dict = dict(zip(self.forward_keys, sample))

        # Create a JIT compiled version of the transform.
        jit_transform = jax.jit(
            lambda data: SpinAnglesToCartesianSpinTransform(
                freq_ref=freq_ref_sample
            ).transform(data)
        )
        jitted_spins, jitted_jacobian = jit_transform(sample_dict)
        non_jitted_spins, non_jitted_jacobian = SpinAnglesToCartesianSpinTransform(
            freq_ref=freq_ref_sample
        ).transform(sample_dict)

        # Remove keys that are not used in the comparison
        for key in ("M_c", "q", "phase_c"):
            jitted_spins.pop(key)
            non_jitted_spins.pop(key)

        # Assert that the jitted and non-jitted results agree
        assert jnp.allclose(
            jnp.array(list(dict(sorted(jitted_spins.items())).values())),
            jnp.array(list(dict(sorted(non_jitted_spins.items())).values())),
        )

        # Also check that the jitted jacobian contains no NaNs
        assert not jnp.isnan(jitted_jacobian).any()

    def test_jitted_backward_transform(self):
        """
        Test that the backward transformation is JIT compilable
        """

        # Generate random sample
        subkeys = jax.random.split(jax.random.PRNGKey(123), 11)

        theta_jn = jax.random.uniform(subkeys[0], (1,), minval=0, maxval=jnp.pi)
        phi_jl = jax.random.uniform(subkeys[1], (1,), minval=0, maxval=2 * jnp.pi)
        tilt_1 = jax.random.uniform(subkeys[2], (1,), minval=0, maxval=jnp.pi)
        tilt_2 = jax.random.uniform(subkeys[3], (1,), minval=0, maxval=jnp.pi)
        phi_12 = jax.random.uniform(subkeys[4], (1,), minval=0, maxval=2 * jnp.pi)
        a_1 = jax.random.uniform(subkeys[5], (1,), minval=0, maxval=1)
        a_2 = jax.random.uniform(subkeys[6], (1,), minval=0, maxval=1)
        M_c = jax.random.uniform(subkeys[7], (1,), minval=1, maxval=100)
        q = jax.random.uniform(subkeys[8], (1,), minval=0.125, maxval=1)
        phase_c = jax.random.uniform(subkeys[9], (1,), minval=0, maxval=2 * jnp.pi)
        f_ref = jax.random.uniform(subkeys[10], (1,), minval=10, maxval=100)

        sample = [
            theta_jn[0],
            phi_jl[0],
            tilt_1[0],
            tilt_2[0],
            phi_12[0],
            a_1[0],
            a_2[0],
            M_c[0],
            q[0],
            phase_c[0],
        ]
        freq_ref_sample = f_ref[0]
        sample_dict = dict(zip(self.backward_keys, sample))

        # Create a JIT compiled version of the transform.
        jit_inverse_transform = jax.jit(
            lambda data: SpinAnglesToCartesianSpinTransform(
                freq_ref=freq_ref_sample
            ).inverse(data)
        )
        jitted_spins, jitted_jacobian = jit_inverse_transform(sample_dict)
        non_jitted_spins, non_jitted_jacobian = SpinAnglesToCartesianSpinTransform(
            freq_ref=freq_ref_sample
        ).inverse(sample_dict)

        # Remove keys that are not used in the comparison
        for key in ("M_c", "q", "phase_c"):
            jitted_spins.pop(key)
            non_jitted_spins.pop(key)

        # Assert that the jitted and non-jitted results agree.
        assert jnp.allclose(
            jnp.array(list(dict(sorted(jitted_spins.items())).values())),
            jnp.array(list(dict(sorted(non_jitted_spins.items())).values())),
        )

        # Also check that the jitted jacobian contains no NaNs
        assert not jnp.isnan(jitted_jacobian).any()


class TestHelperFunctions:
    def test_reverse_bijective_transform(self):
        # Test the reverse_bijective_transform function by applying it to a simple ScaleTransform.
        name_mapping = (["a", "b"], ["a_scaled", "b_scaled"])
        scale = 3.0
        original_transform = ScaleTransform(name_mapping, scale)
        input_data = {"a": 2.0, "b": 4.0}

        # Compute output using original transform.
        output, log_det = original_transform.transform(input_data.copy())
        # Obtain reversed transform.
        reversed_transform = reverse_bijective_transform(original_transform)
        # Now, using the reversed transform (which swaps the transform and its inverse),
        # applying its forward transformation on the original output should recover the original input.
        recovered, rev_log_det = reversed_transform.transform(output.copy())
        assert np.allclose(list(recovered.values()), list(input_data.values()))
        assert np.allclose(rev_log_det, -log_det)
